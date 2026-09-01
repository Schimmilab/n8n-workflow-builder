#!/usr/bin/env python3
"""
N8n Client Module
HTTP client for n8n API interactions
"""
import json
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("n8n-workflow-builder")

# n8n API only accepts these settings keys on PUT /workflows/:id
# Internal properties like 'availableInMCP' or 'binaryMode' cause 400 errors
ALLOWED_SETTINGS_KEYS = {
    "executionOrder", "timezone", "callerPolicy", "errorWorkflow",
    "saveDataSuccessExecution", "saveDataErrorExecution",
    "saveManualExecutions", "saveExecutionProgress"
}


class N8nClient:
    """Client for n8n API"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}
    
    async def get_workflows(self, active_only: bool = False) -> List[Dict]:
        """Get all workflows"""
        params = {}
        if active_only:
            params["active"] = "true"
        
        response = await self.client.get(
            f"{self.api_url}/api/v1/workflows",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]

    async def list_workflows(self, active_only: bool = False) -> List[Dict]:
        """Alias for get_workflows - used by change simulation"""
        return await self.get_workflows(active_only)

    async def get_workflow(self, workflow_id: str) -> Dict:
        """Get a specific workflow"""
        response = await self.client.get(
            f"{self.api_url}/api/v1/workflows/{workflow_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def create_workflow(self, workflow: Dict) -> Dict:
        """Create a new workflow"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/v1/workflows",
                headers=self.headers,
                json=workflow
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Log the detailed error response for debugging
            error_detail = ""
            try:
                error_detail = e.response.text
            except:
                error_detail = str(e)
            logger.error(f"Failed to create workflow: {error_detail}")
            logger.error(f"Payload sent: {json.dumps(workflow, indent=2)}")
            raise Exception(f"Failed to create workflow: {error_detail}")

    async def execute_workflow(self, workflow_id: str, data: Optional[Dict] = None) -> Dict:
        """Execute a workflow (test run)

        Note: This method attempts multiple strategies to execute a workflow:
        1. Check if workflow exists and get its structure
        2. Activate the workflow if it's inactive
        3. Try to trigger via production endpoint (webhook/manual trigger)
        4. Fall back to helpful error message if execution is not possible via API
        """
        try:
            # First, verify the workflow exists
            workflow = await self.get_workflow(workflow_id)

            # Check if workflow is active, activate if needed
            if not workflow.get("active", False):
                logger.info(f"Workflow {workflow_id} is inactive. Activating...")
                await self.update_workflow(workflow_id, {"active": True})

            # Strategy 1: Try POST to /execute endpoint (current n8n API)
            try:
                response = await self.client.post(
                    f"{self.api_url}/api/v1/workflows/{workflow_id}/execute",
                    headers=self.headers,
                    json=data or {}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # 404 = endpoint doesn't exist, 405 = method not allowed (try next strategy)
                if e.response.status_code not in [404, 405]:
                    raise

            # Strategy 2: Try POST to /test endpoint (older versions)
            try:
                response = await self.client.post(
                    f"{self.api_url}/api/v1/workflows/{workflow_id}/test",
                    headers=self.headers,
                    json=data or {}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # 404 = endpoint doesn't exist, 405 = method not allowed (try next strategy)
                if e.response.status_code not in [404, 405]:
                    raise

            # Strategy 3: Check if workflow has a webhook trigger and provide URL
            webhook_url = self._find_webhook_url(workflow)
            if webhook_url:
                return {
                    "success": False,
                    "message": f"This workflow uses a webhook trigger. Trigger it by making a POST request to: {webhook_url}",
                    "webhook_url": webhook_url,
                    "workflow_id": workflow_id,
                    "workflow_name": workflow.get("name", "Unknown")
                }

            # Strategy 4: Check for manual trigger node
            has_manual_trigger = self._has_manual_trigger(workflow)
            if has_manual_trigger:
                # For manual trigger workflows, we need to use the executions endpoint
                try:
                    response = await self.client.post(
                        f"{self.api_url}/api/v1/executions",
                        headers=self.headers,
                        json={
                            "workflowId": workflow_id,
                            "data": data or {}
                        }
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError:
                    pass

            # If all strategies fail, provide helpful error
            trigger_info = self._get_trigger_info(workflow)
            raise Exception(
                f"Cannot execute workflow '{workflow.get('name', workflow_id)}' via API. "
                f"Trigger type: {trigger_info}. "
                f"This workflow needs to be triggered via its configured trigger (webhook, schedule, etc.) "
                f"or manually executed using the n8n UI 'Execute Workflow' button."
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"Workflow {workflow_id} not found. Please verify the workflow ID.")
            raise Exception(f"HTTP error executing workflow: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            if "Cannot execute workflow" in str(e):
                raise
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            raise Exception(f"Failed to execute workflow: {str(e)}")

    def _find_webhook_url(self, workflow: Dict) -> Optional[str]:
        """Find webhook URL if workflow has webhook trigger"""
        nodes = workflow.get("nodes", [])
        for node in nodes:
            node_type = node.get("type", "")
            if "webhook" in node_type.lower():
                # Extract webhook path
                webhook_path = node.get("parameters", {}).get("path", "")
                if webhook_path:
                    # Check if it's a production or test webhook
                    webhook_type = node.get("webhookId", "test")
                    base_path = "webhook" if "prod" in webhook_type else "webhook-test"
                    return f"{self.api_url}/{base_path}/{webhook_path}"
        return None

    def _has_manual_trigger(self, workflow: Dict) -> bool:
        """Check if workflow has manual trigger node"""
        nodes = workflow.get("nodes", [])
        for node in nodes:
            node_type = node.get("type", "").lower()
            if "manualtrigger" in node_type or node_type == "n8n-nodes-base.manualtrigger":
                return True
        return False

    def _get_trigger_info(self, workflow: Dict) -> str:
        """Get human-readable trigger type info"""
        nodes = workflow.get("nodes", [])
        triggers = []
        for node in nodes:
            node_type = node.get("type", "")
            if "trigger" in node_type.lower():
                # Extract readable name
                trigger_name = node_type.split(".")[-1] if "." in node_type else node_type
                triggers.append(trigger_name)

        if triggers:
            return ", ".join(triggers)
        return "Unknown"
    
    async def get_executions(self, workflow_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get workflow executions (summary only, without full node data)"""
        params = {"limit": limit}
        if workflow_id:
            params["workflowId"] = workflow_id

        response = await self.client.get(
            f"{self.api_url}/api/v1/executions",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]

    async def get_execution(self, execution_id: str, include_data: bool = True) -> Dict:
        """Get detailed execution data including all node inputs/outputs

        Args:
            execution_id: The execution ID
            include_data: Whether to include full execution data (default: True)

        Returns:
            Full execution data with node data
        """
        # Add includeData parameter to get full node execution data
        params = {}
        if include_data:
            params['includeData'] = 'true'

        response = await self.client.get(
            f"{self.api_url}/api/v1/executions/{execution_id}",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()

        result = response.json()

        # Log for debugging if data is still missing
        if not result.get('data', {}).get('resultData'):
            logger.warning(f"Execution {execution_id} has no resultData - execution data might not be saved by n8n")

        return result

    async def update_workflow(self, workflow_id: str, updates: Dict, replace_nodes: bool = False) -> Dict:
        """Update an existing workflow

        Args:
            workflow_id: ID of the workflow to update
            updates: Dictionary with fields to update (name, active, nodes, connections, settings, etc.)
            replace_nodes: If True, completely replace nodes instead of merging (removes old nodes)

        Returns:
            Updated workflow data
        """
        # First get the current workflow to merge with updates
        current_workflow = await self.get_workflow(workflow_id)

        # Whitelist of fields that are allowed by n8n API for updates
        # Note: 'active', 'tags', 'id', 'createdAt', 'updatedAt' etc. are read-only
        allowed_fields = ['name', 'nodes', 'connections', 'settings', 'staticData']

        # Build the update payload - start with required fields
        payload = {
            'name': current_workflow.get('name', 'Unnamed Workflow'),
            'nodes': current_workflow.get('nodes', []),
            'connections': current_workflow.get('connections', {}),
        }

        # Add optional allowed fields if they exist in current workflow
        for field in ['settings', 'staticData']:
            if field in current_workflow:
                if field == 'settings':
                    # Filter out internal n8n properties not accepted by PUT API
                    payload[field] = {k: v for k, v in current_workflow[field].items() if k in ALLOWED_SETTINGS_KEYS}
                else:
                    payload[field] = current_workflow[field]

        # Apply updates - only allow whitelisted fields
        for key, value in updates.items():
            if key in allowed_fields:
                # Handle nodes update based on replace_nodes flag
                if key == 'nodes' and isinstance(value, list):
                    if replace_nodes:
                        # Complete replacement: use new nodes directly
                        payload['nodes'] = value
                    else:
                        # Smart merge: update existing nodes by name, add new ones (keeps old nodes)
                        existing_nodes = {node.get('name'): node for node in payload.get('nodes', [])}
                        for update_node in value:
                            node_name = update_node.get('name')
                            if node_name and node_name in existing_nodes:
                                # Merge: update existing node fields
                                existing_nodes[node_name].update(update_node)
                            else:
                                # Add new node
                                existing_nodes[update_node.get('name')] = update_node
                        payload['nodes'] = list(existing_nodes.values())
                # Smart merge for connections: merge connection dicts
                elif key == 'connections' and isinstance(value, dict):
                    if 'connections' not in payload:
                        payload['connections'] = {}
                    for node_name, node_connections in value.items():
                        if node_name not in payload['connections']:
                            payload['connections'][node_name] = node_connections
                        else:
                            # Merge connections for this node
                            for output_type, outputs in node_connections.items():
                                if output_type not in payload['connections'][node_name]:
                                    payload['connections'][node_name][output_type] = outputs
                                else:
                                    payload['connections'][node_name][output_type] = outputs
                # For settings: filter to allowed keys before applying
                elif key == 'settings' and isinstance(value, dict):
                    payload[key] = {k: v for k, v in value.items() if k in ALLOWED_SETTINGS_KEYS}
                # For other fields: simple replace
                else:
                    payload[key] = value
            else:
                logger.warning(f"Skipping field '{key}' - it's read-only or not supported by n8n API")

        # Ensure connections is always present and is a dict
        if 'connections' not in payload or payload['connections'] is None:
            payload['connections'] = {}

        # n8n API uses PUT for updates, not PATCH
        try:
            response = await self.client.put(
                f"{self.api_url}/api/v1/workflows/{workflow_id}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # Log the detailed error response for debugging
            error_detail = ""
            try:
                error_detail = e.response.text
            except:
                error_detail = str(e)
            logger.error(f"Failed to update workflow {workflow_id}: {error_detail}")
            logger.error(f"Payload sent: {json.dumps(payload, indent=2)}")
            raise Exception(f"Failed to update workflow: {error_detail}")

    async def _set_active(self, workflow_id: str, active: bool) -> Dict:
        """Activate or deactivate a workflow via n8n's dedicated endpoints.

        n8n's PATCH /workflows/{id} treats `active` as read-only — the only way
        to toggle it through the API is POST /workflows/{id}/activate resp.
        /deactivate. Verified against the live instance on 2026-09-01: an
        invented route returns 405, while these return 404 with a domain
        message ("You do not have permission to activate this workflow"),
        which is what proves the routes exist.
        """
        verb = "activate" if active else "deactivate"
        try:
            response = await self.client.post(
                f"{self.api_url}/api/v1/workflows/{workflow_id}/{verb}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = e.response.json().get("message", "")
            except Exception:
                detail = e.response.text[:200]
            raise Exception(f"{e.response.status_code}: {detail}") from e

    async def activate_workflow(self, workflow_id: str) -> Dict:
        """Activate a workflow (its triggers start firing)."""
        return await self._set_active(workflow_id, True)

    async def deactivate_workflow(self, workflow_id: str) -> Dict:
        """Deactivate a workflow (its triggers stop firing)."""
        return await self._set_active(workflow_id, False)

    async def delete_workflow(self, workflow_id: str) -> Dict:
        """Delete (archive) a workflow

        Args:
            workflow_id: ID of the workflow to delete

        Returns:
            Success message
        """
        try:
            response = await self.client.delete(
                f"{self.api_url}/api/v1/workflows/{workflow_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return {"success": True, "message": f"Workflow {workflow_id} deleted successfully"}
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except:
                error_detail = str(e)
            logger.error(f"Failed to delete workflow {workflow_id}: {error_detail}")
            raise Exception(f"Failed to delete workflow: {error_detail}")

    async def get_node_types(self) -> List[Dict]:
        """Get list of all available node types

        Returns:
            List of node type metadata including name, displayName, description, version
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/api/v1/node-types",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except:
                error_detail = str(e)
            logger.error(f"Failed to get node types: {error_detail}")
            raise Exception(f"Failed to get node types: {error_detail}")

    async def get_node_type_schema(self, node_type: str) -> Dict:
        """Get detailed schema for a specific node type

        Args:
            node_type: Node type name (e.g., "n8n-nodes-base.googleDrive")

        Returns:
            Complete node schema including:
            - displayName, description, version
            - properties: all available parameters
            - operations: available operations (for resource nodes)
            - credentials: required credential types
            - outputs: output schema
        """
        try:
            response = await self.client.get(
                f"{self.api_url}/api/v1/node-types/{node_type}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"Node type '{node_type}' not found. Use get_node_types() to see available nodes.")
            error_detail = ""
            try:
                error_detail = e.response.text
            except:
                error_detail = str(e)
            logger.error(f"Failed to get node type schema for {node_type}: {error_detail}")
            raise Exception(f"Failed to get node type schema: {error_detail}")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

