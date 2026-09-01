#!/usr/bin/env python3
"""
Workflow Management Tools
Tools for creating, updating, analyzing, and managing n8n workflows
"""
import json
from typing import Any, Dict, List
from mcp.types import TextContent

from .base import BaseTool, ToolError, WorkflowNotFoundError, ValidationError
from ..builders.workflow_builder import NODE_KNOWLEDGE
from ..templates.recommender import WORKFLOW_TEMPLATES


class WorkflowTools(BaseTool):
    """Handler for workflow management tools"""
    
    async def handle(self, name: str, arguments: dict) -> list[TextContent]:
        """Route workflow tool calls to appropriate handler methods
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            List of TextContent responses
        """
        handlers = {
            "suggest_workflow_nodes": self.suggest_workflow_nodes,
            "generate_workflow_template": self.generate_workflow_template,
            "analyze_workflow": self.analyze_workflow,
            "list_workflows": self.list_workflows,
            "get_workflow_details": self.get_workflow_details,
            "create_workflow": self.create_workflow,
            "update_workflow": self.update_workflow,
            "delete_workflow": self.delete_workflow,
            "activate_workflow": self.activate_workflow,
            "deactivate_workflow": self.deactivate_workflow,
            "get_workflow_history": self.get_workflow_history,
            "get_workflow_version": self.get_workflow_version,
            "execute_workflow": self.execute_workflow,
            "get_executions": self.get_executions,
            "get_execution_details": self.get_execution_details,
            "explain_node": self.explain_node,
            "debug_workflow_error": self.debug_workflow_error,
            "validate_workflow": self.validate_workflow,
            "validate_workflow_json": self.validate_workflow_json,
        }
        
        handler = handlers.get(name)
        if not handler:
            raise ToolError("UNKNOWN_TOOL", f"Tool '{name}' not found in workflow tools")
        
        return await handler(arguments)
    
    async def suggest_workflow_nodes(self, args: dict) -> list[TextContent]:
        """Suggest nodes based on workflow description"""
        description = args["description"]
        suggestions = self.deps.workflow_builder.suggest_nodes(description)
        
        if not suggestions:
            return [TextContent(
                type="text",
                text="I couldn't find specific nodes for this description. "
                     "Please describe in more detail what the workflow should do!"
            )]
        
        outline = self.deps.workflow_builder.generate_workflow_outline(description, suggestions)
        return [TextContent(type="text", text=outline)]
    
    async def generate_workflow_template(self, args: dict) -> list[TextContent]:
        """Generate complete workflow template"""
        description = args["description"]
        template_type = args.get("template_type", "custom")
        
        suggestions = self.deps.workflow_builder.suggest_nodes(description)
        outline = self.deps.workflow_builder.generate_workflow_outline(description, suggestions)
        
        # Add template-specific guidance
        if template_type in WORKFLOW_TEMPLATES:
            template = WORKFLOW_TEMPLATES[template_type]
            outline += f"\n## Template: {template['name']}\n\n"
            outline += "Recommended Node Structure:\n"
            for i, node in enumerate(template['nodes'], 1):
                outline += f"{i}. {node['name']} ({node['type']})\n"
        
        return [TextContent(type="text", text=outline)]
    
    async def analyze_workflow(self, args: dict) -> list[TextContent]:
        """Analyze workflow for issues"""
        workflow_id = args["workflow_id"]
        
        try:
            workflow = await self.deps.client.get_workflow(workflow_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to fetch workflow: {str(e)}")
        
        analysis = self.deps.workflow_builder.analyze_workflow(workflow)
        
        # Set as current and log
        self.deps.state_manager.set_current_workflow(workflow['id'], workflow['name'])
        self.deps.state_manager.log_action("analyze_workflow", {
            "workflow_id": workflow_id,
            "complexity": analysis['complexity']
        })
        
        result = f"# Workflow Analysis: {workflow.get('name', workflow_id)}\n\n"
        result += f"**Complexity:** {analysis['complexity']}\n"
        result += f"**Total Nodes:** {analysis['total_nodes']}\n\n"
        
        if analysis['issues']:
            result += "## ⚠️ Issues Found:\n\n"
            for issue in analysis['issues']:
                result += f"- {issue}\n"
            result += "\n"
        
        if analysis['suggestions']:
            result += "## 💡 Suggestions:\n\n"
            for suggestion in analysis['suggestions']:
                result += f"- {suggestion}\n"
        
        if not analysis['issues'] and not analysis['suggestions']:
            result += "✅ Workflow looks good! No major issues found.\n"
        
        return [TextContent(type="text", text=result)]
    
    async def list_workflows(self, args: dict) -> list[TextContent]:
        """List all workflows"""
        active_only = args.get("active_only", False)
        
        try:
            workflows = await self.deps.client.get_workflows(active_only)
        except Exception as e:
            raise ToolError("API_ERROR", f"Failed to list workflows: {str(e)}")
        
        result = f"# Workflows ({len(workflows)} total)\n\n"
        for wf in workflows:
            status = "🟢" if wf.get("active") else "⚪"
            result += f"{status} **{wf['name']}**\n"
            result += f"   ID: `{wf['id']}`\n"
            result += f"   Nodes: {len(wf.get('nodes', []))}\n"
            result += f"   Updated: {wf.get('updatedAt', 'N/A')}\n\n"
        
        return [TextContent(type="text", text=result)]
    
    async def get_workflow_details(self, args: dict) -> list[TextContent]:
        """Get detailed workflow information"""
        workflow_id = args["workflow_id"]
        
        try:
            workflow = await self.deps.client.get_workflow(workflow_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to fetch workflow: {str(e)}")
        
        # Set as current workflow and log action
        self.deps.state_manager.set_current_workflow(workflow['id'], workflow['name'])
        self.deps.state_manager.log_action("get_workflow_details", {
            "workflow_id": workflow_id,
            "workflow_name": workflow['name']
        })
        
        result = f"# Workflow: {workflow['name']}\n\n"
        result += f"**ID:** {workflow['id']}\n"
        result += f"**Active:** {'Yes' if workflow.get('active') else 'No'}\n"
        result += f"**Nodes:** {len(workflow.get('nodes', []))}\n\n"
        
        result += "## Nodes:\n\n"
        for node in workflow.get('nodes', []):
            result += f"### {node['name']} ({node['type']})\n\n"
            
            # Include node parameters
            if 'parameters' in node and node['parameters']:
                result += "**Parameters:**\n```json\n"
                result += json.dumps(node['parameters'], indent=2)
                result += "\n```\n\n"
            
            # Include position info
            if 'position' in node:
                result += f"**Position:** [{node['position'][0]}, {node['position'][1]}]\n\n"
        
        return [TextContent(type="text", text=result)]
    
    async def create_workflow(self, args: dict) -> list[TextContent]:
        """Create a new workflow"""
        name_arg = args["name"]
        nodes = args["nodes"]
        connections = args["connections"]
        settings = args.get("settings", {})
        
        # Build workflow object
        workflow_data = {
            "name": name_arg,
            "nodes": nodes,
            "connections": connections,
            "settings": settings
        }
        
        try:
            created_workflow = await self.deps.client.create_workflow(workflow_data)
        except Exception as e:
            raise ToolError("API_ERROR", f"Failed to create workflow: {str(e)}")
        
        # Set as current workflow and log
        workflow_id = created_workflow["id"]
        self.deps.state_manager.set_current_workflow(workflow_id, name_arg)
        self.deps.state_manager.log_action("create_workflow", {
            "workflow_id": workflow_id,
            "workflow_name": name_arg,
            "node_count": len(nodes)
        })
        
        # Format result
        is_active = created_workflow.get("active", False)
        result = f"# ✅ Workflow Created: {name_arg}\n\n"
        result += f"**ID**: `{workflow_id}`\n"
        result += f"**Status**: {'🟢 Active' if is_active else '⚪ Inactive (default)'}\n"
        result += f"**Nodes**: {len(nodes)}\n"
        result += f"**Connections**: {len(connections)} source nodes\n\n"
        
        result += "## Nodes:\n\n"
        for node in nodes:
            result += f"- **{node['name']}** (`{node['type']}`)\n"
        
        result += "\n---\n\n"
        result += f"💡 **Next Steps**:\n"
        result += f"- Execute with: `execute_workflow(workflow_id=\"{workflow_id}\")`\n"
        result += f"- Monitor with: `watch_workflow_execution(workflow_id=\"{workflow_id}\")`\n"
        if not is_active:
            result += f"- Activate in n8n UI if needed (workflows are inactive by default)\n"
        
        return [TextContent(type="text", text=result)]
    
    async def update_workflow(self, args: dict) -> list[TextContent]:
        """Update an existing workflow"""
        workflow_id = args["workflow_id"]
        replace_nodes = args.get("replace_nodes", False)
        
        # Build updates dictionary from provided arguments
        updates = {}
        if "name" in args:
            updates["name"] = args["name"]
        if "active" in args:
            updates["active"] = args["active"]
        if "nodes" in args:
            updates["nodes"] = args["nodes"]
        if "connections" in args:
            updates["connections"] = args["connections"]
        if "settings" in args:
            updates["settings"] = args["settings"]
        if "tags" in args:
            updates["tags"] = args["tags"]
        
        if not updates:
            return [TextContent(
                type="text",
                text="No updates provided. Please specify at least one field to update (name, active, nodes, connections, settings, or tags)."
            )]
        
        try:
            updated_workflow = await self.deps.client.update_workflow(workflow_id, updates, replace_nodes=replace_nodes)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to update workflow: {str(e)}")
        
        result = f"# Workflow Updated Successfully\n\n"
        result += f"**ID:** {updated_workflow.get('id', 'N/A')}\n"
        result += f"**Name:** {updated_workflow.get('name', 'N/A')}\n"
        result += f"**Active:** {'✅ Yes' if updated_workflow.get('active') else '❌ No'}\n"
        result += f"**Nodes:** {len(updated_workflow.get('nodes', []))}\n"
        result += f"**Updated:** {updated_workflow.get('updatedAt', 'N/A')}\n\n"
        
        result += "## Changes Applied:\n\n"
        for key, value in updates.items():
            if key in ["nodes", "connections"]:
                result += f"- **{key}:** Updated structure\n"
            elif key == "active":
                result += f"- **{key}:** {'Enabled' if value else 'Disabled'}\n"
            else:
                result += f"- **{key}:** {value}\n"
        
        return [TextContent(type="text", text=result)]
    
    async def delete_workflow(self, args: dict) -> list[TextContent]:
        """Delete a workflow"""
        workflow_id = args["workflow_id"]
        
        # Get workflow name before deletion
        try:
            workflow = await self.deps.client.get_workflow(workflow_id)
            workflow_name = workflow.get('name', 'Unknown')
        except:
            workflow_name = "Unknown"
        
        try:
            await self.deps.client.delete_workflow(workflow_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to delete workflow: {str(e)}")
        
        self.deps.state_manager.log_action("delete_workflow", {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name
        })
        
        result = f"# Workflow Deleted Successfully\n\n"
        result += f"**ID:** {workflow_id}\n"
        result += f"**Name:** {workflow_name}\n\n"
        result += "⚠️ The workflow has been removed from n8n."
        
        return [TextContent(type="text", text=result)]
    
    async def get_workflow_history(self, args: dict) -> list[TextContent]:
        """List the saved versions of a workflow, newest first."""
        workflow_id = args.get("workflow_id")
        if not workflow_id:
            raise ToolError("MISSING_PARAMETER", "workflow_id is required")

        try:
            current = await self.deps.client.get_workflow(workflow_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to read workflow: {str(e)}")

        try:
            versions = await self.deps.client.get_workflow_history(workflow_id)
        except Exception as e:
            if "403" in str(e):
                raise ToolError(
                    "NOT_LICENSED",
                    "Workflow history is not available on this n8n instance "
                    f"(the API answered: {str(e)[:120]})"
                )
            raise ToolError("API_ERROR", f"Failed to read history: {str(e)}")

        name = current.get("name", "Unknown")
        if not versions:
            return [TextContent(type="text", text=(
                f"# No version history\n\n**{name}** (`{workflow_id}`) has no saved "
                "versions yet. n8n records one each time the workflow is saved."
            ))]

        versions = sorted(versions, key=lambda v: v.get("createdAt") or "", reverse=True)
        out = [f"# Version History: {name}\n",
               f"**Workflow ID:** `{workflow_id}` · **{len(versions)} version(s)**\n",
               "| # | versionId | created | authors |",
               "|---|---|---|---|"]
        for i, v in enumerate(versions, 1):
            out.append(
                f"| {i} | `{v.get('versionId', '?')}` "
                f"| {(v.get('createdAt') or '?')[:19].replace('T', ' ')} "
                f"| {v.get('authors') or '—'} |"
            )
        out.append(
            "\n💡 Fetch one with: "
            f'`get_workflow_version(workflow_id="{workflow_id}", version_id="…")` '
            "— it also reports what changed against the current state."
        )
        return [TextContent(type="text", text="\n".join(out))]

    async def get_workflow_version(self, args: dict) -> list[TextContent]:
        """Fetch one historic version and diff its node set against the current one.

        ⛔ Deliberately more than a JSON dump: on its own, an old version answers
        "what did it look like" but not "what changed" — and the second question
        is the one anyone actually opens a history for.
        """
        workflow_id = args.get("workflow_id")
        version_id = args.get("version_id")
        if not workflow_id or not version_id:
            raise ToolError("MISSING_PARAMETER", "workflow_id and version_id are required")

        try:
            old = await self.deps.client.get_workflow_version(workflow_id, version_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "VERSION_NOT_FOUND",
                    f"Version '{version_id}' not found for workflow '{workflow_id}'",
                    details={"workflow_id": workflow_id, "version_id": version_id}
                )
            if "403" in str(e):
                raise ToolError("NOT_LICENSED", f"Not available on this instance: {str(e)[:120]}")
            raise ToolError("API_ERROR", f"Failed to read version: {str(e)}")

        try:
            current = await self.deps.client.get_workflow(workflow_id)
        except Exception:
            current = {}

        alt_nodes = {n.get("name") for n in (old.get("nodes") or [])}
        neu_nodes = {n.get("name") for n in (current.get("nodes") or [])}
        entfernt = sorted(alt_nodes - neu_nodes)
        hinzu = sorted(neu_nodes - alt_nodes)

        out = [f"# Workflow Version `{version_id}`\n",
               f"**Name at the time:** {old.get('name') or current.get('name') or 'Unknown'}",
               f"**Saved:** {(old.get('createdAt') or '?')[:19].replace('T', ' ')}",
               f"**Authors:** {old.get('authors') or '—'}",
               f"**Nodes in this version:** {len(alt_nodes)}\n"]

        if not current:
            out.append("⚠️ Current workflow could not be read — no comparison possible.")
        elif not entfernt and not hinzu:
            out.append(f"## Compared to now\n\nSame node set as the current workflow "
                       f"({len(neu_nodes)} nodes). ⚠️ Node *parameters* are not compared — "
                       "identical names do not prove identical content.")
        else:
            out.append(f"## Compared to now ({len(neu_nodes)} nodes currently)\n")
            if entfernt:
                out.append("**Existed then, gone now:**")
                out += [f"- `{n}`" for n in entfernt]
            if hinzu:
                out.append("\n**Added since:**")
                out += [f"- `{n}`" for n in hinzu]
            out.append("\n⚠️ Only node *names* are compared — a renamed node looks "
                       "like one removed plus one added.")

        return [TextContent(type="text", text="\n".join(out))]

    async def _toggle_workflow(self, args: dict, activate: bool) -> list[TextContent]:
        """Shared implementation for activate_workflow / deactivate_workflow.

        Reports the state BEFORE and AFTER the call rather than just "success":
        a 200 from n8n only proves the request was accepted, not that the flag
        actually flipped.
        """
        workflow_id = args.get("workflow_id")
        if not workflow_id:
            raise ToolError("MISSING_PARAMETER", "workflow_id is required")

        verb = "activate" if activate else "deactivate"

        try:
            before = await self.deps.client.get_workflow(workflow_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to read workflow: {str(e)}")

        was_active = bool(before.get("active"))
        name = before.get("name", "Unknown")

        if was_active == activate:
            return [TextContent(type="text", text=(
                f"# No change needed\n\n"
                f"**{name}** (`{workflow_id}`) is already "
                f"{'active' if activate else 'inactive'}. Nothing was sent to n8n."
            ))]

        try:
            if activate:
                await self.deps.client.activate_workflow(workflow_id)
            else:
                await self.deps.client.deactivate_workflow(workflow_id)
        except Exception as e:
            raise ToolError("API_ERROR", f"Failed to {verb} workflow: {str(e)}")

        after = await self.deps.client.get_workflow(workflow_id)
        is_active = bool(after.get("active"))

        if is_active != activate:
            raise ToolError(
                "STATE_NOT_APPLIED",
                f"n8n accepted the {verb} request but the workflow is still "
                f"{'active' if is_active else 'inactive'}. Nothing was changed.",
                details={"workflow_id": workflow_id}
            )

        self.deps.state_manager.log_action(f"{verb}_workflow", {
            "workflow_id": workflow_id,
            "workflow_name": name,
            "active_before": was_active,
            "active_after": is_active
        })

        return [TextContent(type="text", text=(
            f"# Workflow {'Activated' if activate else 'Deactivated'}\n\n"
            f"**Name:** {name}\n"
            f"**ID:** `{workflow_id}`\n"
            f"**active:** {was_active} → {is_active}\n\n"
            + ("⚠️ Its triggers are now live."
               if activate else "The workflow no longer reacts to its triggers.")
        ))]

    async def activate_workflow(self, args: dict) -> list[TextContent]:
        return await self._toggle_workflow(args, activate=True)

    async def deactivate_workflow(self, args: dict) -> list[TextContent]:
        return await self._toggle_workflow(args, activate=False)

    async def execute_workflow(self, args: dict) -> list[TextContent]:
        """Execute a workflow"""
        workflow_id = args["workflow_id"]
        input_data = args.get("input_data")
        
        try:
            execution = await self.deps.client.execute_workflow(workflow_id, input_data)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to execute workflow: {str(e)}")
        
        # Log execution
        execution_id = execution.get('id', 'N/A')
        self.deps.state_manager.set_last_execution(execution_id)
        self.deps.state_manager.log_action("execute_workflow", {
            "workflow_id": workflow_id,
            "execution_id": execution_id
        })
        
        result = f"# Workflow Execution\n\n"
        result += f"**Execution ID:** {execution_id}\n"
        result += f"**Status:** {execution.get('finished', 'Running')}\n"
        result += f"**Data:** {json.dumps(execution.get('data', {}), indent=2)}\n"
        
        return [TextContent(type="text", text=result)]
    
    async def get_executions(self, args: dict) -> list[TextContent]:
        """Get workflow execution history"""
        workflow_id = args.get("workflow_id")
        limit = args.get("limit", 10)
        
        try:
            executions = await self.deps.client.get_executions(workflow_id, limit)
        except Exception as e:
            raise ToolError("API_ERROR", f"Failed to get executions: {str(e)}")
        
        result = f"# Recent Executions ({len(executions)})\n\n"
        for exec in executions:
            status = "✅" if exec.get('finished') else "⏳"
            result += f"{status} **Execution {exec['id']}**\n"
            result += f"   Workflow: {exec.get('workflowData', {}).get('name', 'N/A')}\n"
            result += f"   Started: {exec.get('startedAt', 'N/A')}\n"
            if exec.get('stoppedAt'):
                result += f"   Duration: {exec.get('stoppedAt', 'N/A')}\n"
            result += "\n"
        
        return [TextContent(type="text", text=result)]
    
    async def get_execution_details(self, args: dict) -> list[TextContent]:
        """Get detailed execution information"""
        execution_id = args["execution_id"]
        
        try:
            execution = await self.deps.client.get_execution(execution_id)
        except Exception as e:
            if "404" in str(e):
                raise ToolError(
                    "EXECUTION_NOT_FOUND",
                    f"Execution '{execution_id}' not found",
                    execution_id=execution_id
                )
            raise ToolError("API_ERROR", f"Failed to get execution details: {str(e)}")
        
        result = f"# Execution Details: {execution_id}\n\n"
        result += f"**Workflow:** {execution.get('workflowData', {}).get('name', 'N/A')}\n"
        result += f"**Status:** {'✅ Finished' if execution.get('finished') else '⏳ Running'}\n"
        result += f"**Started:** {execution.get('startedAt', 'N/A')}\n"
        
        if execution.get('stoppedAt'):
            result += f"**Stopped:** {execution.get('stoppedAt', 'N/A')}\n"
        
        if execution.get('mode'):
            result += f"**Mode:** {execution.get('mode')}\n"
        
        # Show node execution data
        exec_data = execution.get('data', {})
        result_data = exec_data.get('resultData', {})
        run_data = result_data.get('runData', {}) if result_data else {}
        
        if run_data:
            result += "\n## Node Results:\n\n"
            for node_name, node_runs in run_data.items():
                result += f"### {node_name}\n"
                for idx, run in enumerate(node_runs):
                    result += f"**Run {idx + 1}:**\n"
                    if 'data' in run:
                        main_data = run['data'].get('main', [[]])[0]
                        if main_data:
                            result += f"- Output items: {len(main_data)}\n"
                            if main_data and len(main_data) > 0:
                                first_item = main_data[0]
                                result += f"- Sample data: `{json.dumps(first_item.get('json', {}), indent=2)[:500]}...`\n"
                    if 'error' in run:
                        result += f"- ❌ Error: {run['error'].get('message', 'Unknown error')}\n"
                result += "\n"
        else:
            result += "\n⚠️ **No node execution data available.**\n\n"
            result += "This can happen if:\n"
            result += "- n8n is configured to not save execution data (check Settings > Executions)\n"
            result += "- The execution data has been pruned/deleted\n"
            result += "- The workflow hasn't been executed yet\n\n"
            result += "To see execution data, ensure 'Save manual executions' and 'Save execution progress' are enabled in n8n settings.\n"
        
        return [TextContent(type="text", text=result)]
    
    async def explain_node(self, args: dict) -> list[TextContent]:
        """Explain a node type from knowledge base"""
        node_type = args["node_type"].lower()
        
        # Search in knowledge base
        explanation = None
        for category in NODE_KNOWLEDGE.values():
            if node_type in category:
                explanation = category[node_type]
                break
        
        if not explanation:
            return [TextContent(
                type="text",
                text=f"Node type '{node_type}' not found in knowledge base. "
                     f"Try: {', '.join(list(NODE_KNOWLEDGE['triggers'].keys()) + list(NODE_KNOWLEDGE['logic'].keys()))}"
            )]
        
        result = f"# {explanation['name']} Node\n\n"
        result += f"**Description:** {explanation['desc']}\n\n"
        result += "## Use Cases:\n\n"
        for use_case in explanation['use_cases']:
            result += f"- {use_case}\n"
        result += "\n## Best Practices:\n\n"
        for practice in explanation['best_practices']:
            result += f"- {practice}\n"
        
        return [TextContent(type="text", text=result)]
    
    async def debug_workflow_error(self, args: dict) -> list[TextContent]:
        """Debug workflow errors"""
        error_msg = args["error_message"]
        node_type = args.get("node_type", "").lower()
        
        debug_info = f"# Workflow Error Debug\n\n"
        debug_info += f"**Error Message:** {error_msg}\n\n"
        
        # Common error patterns
        if "timeout" in error_msg.lower():
            debug_info += "## Probable Cause: Timeout\n\n"
            debug_info += "**Solutions:**\n"
            debug_info += "- Increase timeout setting in node configuration\n"
            debug_info += "- Check if external service is responding slowly\n"
            debug_info += "- Add retry logic\n"
        
        elif "authentication" in error_msg.lower() or "401" in error_msg:
            debug_info += "## Probable Cause: Authentication Error\n\n"
            debug_info += "**Solutions:**\n"
            debug_info += "- Check credentials are correct\n"
            debug_info += "- Verify API key hasn't expired\n"
            debug_info += "- Ensure correct authentication method\n"
        
        elif "404" in error_msg:
            debug_info += "## Probable Cause: Resource Not Found\n\n"
            debug_info += "**Solutions:**\n"
            debug_info += "- Verify URL is correct\n"
            debug_info += "- Check if resource ID exists\n"
            debug_info += "- Confirm API endpoint path\n"
        
        elif "rate limit" in error_msg.lower() or "429" in error_msg:
            debug_info += "## Probable Cause: Rate Limiting\n\n"
            debug_info += "**Solutions:**\n"
            debug_info += "- Add delay between requests\n"
            debug_info += "- Implement exponential backoff\n"
            debug_info += "- Batch requests if possible\n"
        
        else:
            debug_info += "## Generic Troubleshooting Steps:\n\n"
            debug_info += "1. Check node configuration\n"
            debug_info += "2. Verify input data format\n"
            debug_info += "3. Enable workflow logging\n"
            debug_info += "4. Test with minimal data\n"
            debug_info += "5. Check n8n logs for details\n"
        
        return [TextContent(type="text", text=debug_info)]
    
    async def validate_workflow(self, args: dict) -> list[TextContent]:
        """Validate workflow structure"""
        workflow_id = args["workflow_id"]
        
        try:
            workflow = await self.deps.client.get_workflow(workflow_id)
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ToolError(
                    "WORKFLOW_NOT_FOUND",
                    f"Workflow '{workflow_id}' not found",
                    details={"workflow_id": workflow_id}
                )
            raise ToolError("API_ERROR", f"Failed to fetch workflow: {str(e)}")
        
        # Use workflow validator
        validation_result = self.deps.workflow_validator.validate(workflow)
        
        result = f"# Workflow Validation: {workflow.get('name', workflow_id)}\n\n"
        result += f"**Status:** {'✅ Valid' if validation_result['valid'] else '❌ Invalid'}\n\n"
        
        if validation_result.get('errors'):
            result += "## Errors:\n\n"
            for error in validation_result['errors']:
                result += f"- {error}\n"
            result += "\n"
        
        if validation_result.get('warnings'):
            result += "## Warnings:\n\n"
            for warning in validation_result['warnings']:
                result += f"- {warning}\n"
        
        return [TextContent(type="text", text=result)]
    
    async def validate_workflow_json(self, args: dict) -> list[TextContent]:
        """Validate workflow JSON structure"""
        workflow_json = args["workflow_json"]
        
        try:
            workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
        except json.JSONDecodeError as e:
            raise ToolError("VALIDATION_ERROR", f"Invalid JSON: {str(e)}")
        
        # Use workflow validator
        validation_result = self.deps.workflow_validator.validate(workflow)
        
        result = f"# Workflow JSON Validation\n\n"
        result += f"**Status:** {'✅ Valid' if validation_result['valid'] else '❌ Invalid'}\n\n"
        
        if validation_result.get('errors'):
            result += "## Errors:\n\n"
            for error in validation_result['errors']:
                result += f"- {error}\n"
            result += "\n"
        
        if validation_result.get('warnings'):
            result += "## Warnings:\n\n"
            for warning in validation_result['warnings']:
                result += f"- {warning}\n"
        
        return [TextContent(type="text", text=result)]
