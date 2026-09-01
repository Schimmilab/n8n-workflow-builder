#!/usr/bin/env python3
"""
n8n Workflow Builder MCP Server
Advanced MCP server for n8n workflow creation, optimization, and management
"""
import asyncio
import json
import logging
import os
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

# Import all components from refactored modules
from .client import N8nClient
from .state import StateManager
from .validators.workflow_validator import WorkflowValidator
from .validators.semantic_analyzer import SemanticWorkflowAnalyzer
from .analyzers.feedback_analyzer import AIFeedbackAnalyzer
from .security.rbac import RBACManager
from .security.audit import SecurityAuditor
from .templates.recommender import TemplateRecommendationEngine, WORKFLOW_TEMPLATES
from .builders.workflow_builder import WorkflowBuilder, NODE_KNOWLEDGE
from .intent import IntentManager
from .execution.error_analyzer import (
    ExecutionMonitor,
    ErrorContextExtractor,
    ErrorSimplifier,
    FeedbackGenerator
)
from .drift.detector import (
    DriftDetector,
    DriftPatternAnalyzer,
    DriftRootCauseAnalyzer,
    DriftFixSuggester
)
from .drift.analyzers import (
    SchemaDriftAnalyzer,
    RateLimitDriftAnalyzer,
    DataQualityDriftAnalyzer
)
from .explainability import (
    WorkflowExplainer,
    WorkflowPurposeAnalyzer,
    DataFlowTracer,
    DependencyMapper,
    RiskAnalyzer,
    ExplainabilityFormatter
)
from .changes import (
    WorkflowDiffEngine,
    ChangeImpactAnalyzer,
    DryRunSimulator,
    ApprovalWorkflow,
    ChangeFormatter
)
from .templates import (
    TemplateRegistry,
    TemplateIntentExtractor,
    TemplateMatcher,
    TemplateAdapter,
    ProvenanceTracker
)
from .templates.tools import TemplateManager
from .migration import (
    NodeVersionChecker,
    MigrationEngine,
    WorkflowUpdater,
    MigrationReporter,
    MIGRATION_RULES
)
from .node_discovery import NodeDiscovery, NodeRecommender
from .documentation import N8nDocumentation

# NEW: Refactored architecture
from .dependencies import Dependencies
from .tools.workflow_tools import WorkflowTools
from .tools.security_tools import SecurityTools
from .tools.template_tools import TemplateTools
from .tools.execution_tools import ExecutionTools
from .tools.drift_tools import DriftTools
from .tools.explainability_tools import ExplainabilityTools
from .tools.session_tools import SessionTools
from .tools.migration_tools import MigrationTools
from .tools.change_impact_tools import ChangeImpactTools
from .tools.documentation_tools import DocumentationTools
from .tools.advanced_template_tools import AdvancedTemplateTools
from .tools.miscellaneous_tools import MiscellaneousTools
from .tools.validation_tools import ValidationTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("n8n-workflow-builder")


def create_n8n_server(api_url: str, api_key: str) -> Server:
    """Create the n8n workflow builder MCP server"""

    server = Server("n8n-workflow-builder")
    n8n_client = N8nClient(api_url, api_key)
    workflow_builder = WorkflowBuilder()
    workflow_validator = WorkflowValidator()
    semantic_analyzer = SemanticWorkflowAnalyzer()
    template_manager = TemplateManager()
    ai_feedback_analyzer = AIFeedbackAnalyzer()
    state_manager = StateManager()
    rbac_manager = RBACManager()
    security_auditor = SecurityAuditor()
    template_engine = TemplateRecommendationEngine()
    intent_manager = IntentManager()
    approval_workflow = ApprovalWorkflow()

    # Template System v2.0
    template_registry = TemplateRegistry()
    template_adapter = TemplateAdapter()
    provenance_tracker = ProvenanceTracker()

    # Migration System
    workflow_updater = WorkflowUpdater(MIGRATION_RULES)
    migration_reporter = MigrationReporter()

    # Node Discovery System (learns from workflows)
    node_discovery = NodeDiscovery()
    node_recommender = None  # Initialized after first workflow analysis

    # Documentation System
    n8n_docs = N8nDocumentation()

    # NEW: Refactored architecture - wrap existing dependencies
    # This allows gradual migration to new structure
    deps = Dependencies.from_server(
        client=n8n_client,
        state_manager=state_manager,
        workflow_builder=workflow_builder,
        workflow_validator=workflow_validator,
        semantic_analyzer=semantic_analyzer,
        ai_feedback_analyzer=ai_feedback_analyzer,
        security_auditor=security_auditor,
        template_manager=template_manager,
        template_engine=template_engine,
        template_registry=template_registry,
        template_adapter=template_adapter,
        provenance_tracker=provenance_tracker,
        intent_manager=intent_manager,
        workflow_updater=workflow_updater,
        migration_reporter=migration_reporter,
        node_discovery=node_discovery,
        node_recommender=node_recommender,
        n8n_docs=n8n_docs,
        approval_workflow=approval_workflow,
        rbac_manager=rbac_manager
    )
    
    # Initialize tool handlers with dependencies
    workflow_tools = WorkflowTools(deps)
    security_tools = SecurityTools(deps)
    template_tools = TemplateTools(deps)
    execution_tools = ExecutionTools(deps)
    drift_tools = DriftTools(deps)
    explainability_tools = ExplainabilityTools(deps)
    session_tools = SessionTools(deps)
    migration_tools = MigrationTools(deps)
    change_impact_tools = ChangeImpactTools(deps)
    documentation_tools = DocumentationTools(deps)
    advanced_template_tools = AdvancedTemplateTools(deps)
    miscellaneous_tools = MiscellaneousTools(deps)
    validation_tools = ValidationTools(deps)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available n8n workflow tools"""
        return [
            Tool(
                name="suggest_workflow_nodes",
                description=(
                    "🧠 AI-powered node suggestion based on workflow description. "
                    "Analyzes your workflow requirements and suggests the best n8n nodes to use, "
                    "including best practices and common pitfalls to avoid."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of what you want to build"
                        }
                    },
                    "required": ["description"]
                }
            ),
            Tool(
                name="generate_workflow_template",
                description=(
                    "🏗️ Generate a complete workflow template from description. "
                    "Creates a structured workflow outline with recommended nodes, connections, "
                    "and configuration tips."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "What the workflow should do"
                        },
                        "template_type": {
                            "type": "string",
                            "description": "Optional: api_endpoint, scheduled_report, data_sync",
                            "enum": ["api_endpoint", "scheduled_report", "data_sync", "custom"]
                        }
                    },
                    "required": ["description"]
                }
            ),
            Tool(
                name="analyze_workflow",
                description=(
                    "🔍 Analyze an existing workflow for issues and optimization opportunities. "
                    "Checks for common problems, security issues, and suggests improvements."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "ID of the workflow to analyze"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="list_workflows",
                description=(
                    "📋 List all workflows with filtering options. "
                    "Get an overview of your workflows with status and basic info."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "active_only": {
                            "type": "boolean",
                            "description": "Only show active workflows",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="create_workflow",
                description=(
                    "✨ Create a new workflow in n8n. Provide workflow name, nodes, and connections. "
                    "This is the primary tool for building new workflows. "
                    "Note: Workflows are created inactive by default and must be activated in the n8n UI."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Workflow name"
                        },
                        "nodes": {
                            "type": "array",
                            "description": "Array of workflow nodes with type, name, parameters, position",
                            "items": {"type": "object"}
                        },
                        "connections": {
                            "type": "object",
                            "description": "Workflow connections between nodes"
                        },
                        "settings": {
                            "type": "object",
                            "description": "Optional workflow settings"
                        }
                    },
                    "required": ["name", "nodes", "connections"]
                }
            ),
            Tool(
                name="get_workflow_details",
                description=(
                    "📄 Get detailed information about a specific workflow including "
                    "all nodes, connections, and configuration."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="activate_workflow",
                description=(
                    "▶️ Activate a workflow so its triggers start firing. "
                    "Uses n8n's dedicated POST /workflows/{id}/activate endpoint — "
                    "the 'active' field is read-only via update_workflow. "
                    "Reports the active state before and after, and fails loudly "
                    "if n8n accepted the request without the flag actually flipping."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "ID of the workflow to activate"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="deactivate_workflow",
                description=(
                    "⏸️ Deactivate a workflow so its triggers stop firing. "
                    "Uses n8n's dedicated POST /workflows/{id}/deactivate endpoint. "
                    "Reports the active state before and after."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "ID of the workflow to deactivate"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="execute_workflow",
                description=(
                    "▶️ Execute a workflow with optional input data. "
                    "Trigger a workflow manually and get execution results."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to execute"
                        },
                        "input_data": {
                            "type": "object",
                            "description": "Optional input data as JSON"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="get_executions",
                description=(
                    "📊 Get execution history for workflows. "
                    "View past executions with status, duration, and error info. "
                    "Note: This returns summary data only. Use get_execution_details for full node data."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Optional: Filter by workflow ID"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Number of executions to return (default: 10)",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="get_execution_details",
                description=(
                    "🔍 Get detailed execution data including all node inputs and outputs. "
                    "Use this to see what data each node processed during an execution."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {
                            "type": "string",
                            "description": "Execution ID to get details for"
                        }
                    },
                    "required": ["execution_id"]
                }
            ),
            Tool(
                name="explain_node",
                description=(
                    "📚 Get detailed explanation of a specific n8n node type, "
                    "including use cases, configuration tips, and examples."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "string",
                            "description": "Node type (e.g., 'webhook', 'http_request', 'if', 'slack')"
                        }
                    },
                    "required": ["node_type"]
                }
            ),
            Tool(
                name="debug_workflow_error",
                description=(
                    "🐛 Help debug a workflow error. Analyzes error messages and "
                    "suggests potential fixes and troubleshooting steps."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "error_message": {
                            "type": "string",
                            "description": "The error message or description"
                        },
                        "node_type": {
                            "type": "string",
                            "description": "Optional: The node type where error occurred"
                        }
                    },
                    "required": ["error_message"]
                }
            ),
            Tool(
                name="update_workflow",
                description=(
                    "✏️ Update an existing workflow. Modify workflow properties like name, "
                    "nodes, connections, or settings. Can rename workflows or make structural changes. "
                    "Note: The 'active' field is read-only and cannot be changed via API - use the n8n UI instead. "
                    "IMPORTANT: By default, nodes are MERGED (old nodes kept). Use replace_nodes=true to completely replace (removes old ones)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "ID of the workflow to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional: New name for the workflow"
                        },
                        "nodes": {
                            "type": "array",
                            "description": "Optional: Updated nodes array (full node structure)"
                        },
                        "connections": {
                            "type": "object",
                            "description": "Optional: Updated connections object"
                        },
                        "settings": {
                            "type": "object",
                            "description": "Optional: Workflow settings"
                        },
                        "replace_nodes": {
                            "type": "boolean",
                            "description": "Optional: If true, completely replace all nodes (removes old ones). Default: false (merges)"
                        },
                        "tags": {
                            "type": "array",
                            "description": "Optional: Workflow tags"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="delete_workflow",
                description=(
                    "🗑️ Delete (archive) a workflow. This removes the workflow from n8n. "
                    "Use with caution as this action may be irreversible depending on n8n configuration."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "ID of the workflow to delete"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="get_session_state",
                description=(
                    "🔄 Get current session state and context. "
                    "Shows the currently active workflow, recent workflows, and action history. "
                    "Use this to understand what you were working on."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="set_active_workflow",
                description=(
                    "📌 Set a workflow as the active/current workflow for the session. "
                    "This allows you to reference it later with 'current workflow' instead of IDs."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to set as active"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="get_active_workflow",
                description=(
                    "📍 Get the currently active workflow that was set via set_active_workflow. "
                    "Returns ID and name of the active workflow."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_recent_workflows",
                description=(
                    "📜 Get a list of recently accessed workflows. "
                    "Shows the last 10 workflows you worked with, ordered by most recent."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_session_history",
                description=(
                    "📝 Get recent action history for this session. "
                    "Shows what operations were performed recently."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Number of history entries to return (default: 10)",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="clear_session_state",
                description=(
                    "🗑️ Clear all session state and history. "
                    "Resets the active workflow, recent workflows, and action history."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="validate_workflow",
                description=(
                    "✅ Validate a workflow before deployment. "
                    "Performs comprehensive validation: schema checks, semantic rules, "
                    "node parameter validation, security checks, and best practices. "
                    "Returns detailed errors and warnings."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to validate"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="validate_workflow_json",
                description=(
                    "✅ Validate a workflow from JSON structure. "
                    "Use this to validate a workflow before creating it. "
                    "Accepts raw workflow JSON and returns validation results."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow": {
                            "type": "object",
                            "description": "Workflow JSON object with nodes, connections, etc."
                        }
                    },
                    "required": ["workflow"]
                }
            ),
            Tool(
                name="analyze_workflow_semantics",
                description=(
                    "🔬 Deep semantic analysis of workflow logic and patterns. "
                    "Goes beyond schema validation to detect anti-patterns, logic errors, "
                    "security issues, and performance problems. Provides LLM-friendly fix suggestions. "
                    "Checks: HTTP retry patterns, loop completeness, timezone config, IF node paths, "
                    "webhook security, infinite loops, credential usage, N+1 queries, rate limiting, "
                    "data validation, and more. Returns copy-paste ready code fixes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to analyze"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="analyze_execution_errors",
                description=(
                    "🔍 Analyze execution errors and provide AI-friendly feedback. "
                    "Examines failed workflow executions, identifies root causes, "
                    "and generates structured feedback with fix suggestions. "
                    "Perfect for debugging and learning from failures."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {
                            "type": "string",
                            "description": "Execution ID to analyze"
                        }
                    },
                    "required": ["execution_id"]
                }
            ),
            Tool(
                name="get_workflow_improvement_suggestions",
                description=(
                    "💡 Get improvement suggestions for a failed workflow. "
                    "Analyzes errors and generates specific recommendations "
                    "for fixing nodes, adding missing features, and improving reliability."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "execution_id": {
                            "type": "string",
                            "description": "Failed execution ID to analyze"
                        },
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID for context"
                        }
                    },
                    "required": ["execution_id", "workflow_id"]
                }
            ),
            Tool(
                name="rbac_get_status",
                description=(
                    "🔒 Get RBAC and security status report. "
                    "Shows users, roles, tenants, pending approvals, and recent audit log. "
                    "Use this to understand the current security configuration."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="rbac_add_user",
                description=(
                    "👤 Add a new user with specific role and tenant. "
                    "Creates a user account with assigned permissions based on role. "
                    "Roles: admin, developer, operator, viewer, auditor"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username for the new user"
                        },
                        "role": {
                            "type": "string",
                            "description": "Role (admin, developer, operator, viewer, auditor)",
                            "enum": ["admin", "developer", "operator", "viewer", "auditor"]
                        },
                        "tenant_id": {
                            "type": "string",
                            "description": "Tenant ID (default: 'default')",
                            "default": "default"
                        }
                    },
                    "required": ["username", "role"]
                }
            ),
            Tool(
                name="rbac_get_user_info",
                description=(
                    "ℹ️ Get detailed information about a user. "
                    "Shows username, role, permissions, tenant, and creation date."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username to query"
                        }
                    },
                    "required": ["username"]
                }
            ),
            Tool(
                name="rbac_check_permission",
                description=(
                    "✅ Check if a user has a specific permission. "
                    "Validates whether the user's role grants access to an operation. "
                    "Examples: workflow.create, workflow.delete, approval.approve"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username to check"
                        },
                        "permission": {
                            "type": "string",
                            "description": "Permission to check (e.g., 'workflow.create', 'approval.approve')"
                        }
                    },
                    "required": ["username", "permission"]
                }
            ),
            Tool(
                name="rbac_create_approval_request",
                description=(
                    "📝 Create an approval request for a critical operation. "
                    "Used when developer needs admin approval for operations like workflow.delete. "
                    "Returns approval_id for tracking."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username requesting approval"
                        },
                        "operation": {
                            "type": "string",
                            "description": "Operation requiring approval (workflow.delete, workflow.deploy_production, etc.)"
                        },
                        "details": {
                            "type": "object",
                            "description": "Additional details about the operation (workflow_id, reason, etc.)"
                        }
                    },
                    "required": ["username", "operation", "details"]
                }
            ),
            Tool(
                name="rbac_approve_request",
                description=(
                    "✅ Approve a pending approval request. "
                    "Admin approves a request from developer. Cannot approve own requests."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "approval_id": {
                            "type": "string",
                            "description": "Approval request ID to approve"
                        },
                        "approver": {
                            "type": "string",
                            "description": "Username of approver (must have approval.approve permission)"
                        }
                    },
                    "required": ["approval_id", "approver"]
                }
            ),
            Tool(
                name="rbac_reject_request",
                description=(
                    "❌ Reject a pending approval request. "
                    "Admin rejects a request with reason. Logged in audit trail."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "approval_id": {
                            "type": "string",
                            "description": "Approval request ID to reject"
                        },
                        "rejector": {
                            "type": "string",
                            "description": "Username of rejector"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for rejection"
                        }
                    },
                    "required": ["approval_id", "rejector"]
                }
            ),
            Tool(
                name="rbac_get_pending_approvals",
                description=(
                    "⏳ Get list of pending approval requests. "
                    "Shows all pending requests, or filtered by username if provided."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Optional: Filter by username (shows requests by/for this user)"
                        }
                    }
                }
            ),
            Tool(
                name="rbac_create_tenant",
                description=(
                    "🏢 Create a new tenant for multi-tenant isolation. "
                    "Each tenant has separate workflows, users, and audit logs."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tenant_id": {
                            "type": "string",
                            "description": "Unique tenant identifier (e.g., 'acme-corp')"
                        },
                        "name": {
                            "type": "string",
                            "description": "Display name for tenant (e.g., 'ACME Corporation')"
                        }
                    },
                    "required": ["tenant_id", "name"]
                }
            ),
            Tool(
                name="rbac_get_audit_log",
                description=(
                    "📋 Get audit log with optional filters. "
                    "Shows security-relevant actions (user created, workflow deleted, approvals, etc.). "
                    "Last 500 events stored, customizable retention."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Number of log entries to return (default: 50)",
                            "default": 50
                        },
                        "username": {
                            "type": "string",
                            "description": "Optional: Filter by username"
                        },
                        "action": {
                            "type": "string",
                            "description": "Optional: Filter by action type"
                        }
                    }
                }
            ),
            Tool(
                name="recommend_templates",
                description=(
                    "🎯 Get AI-powered template recommendations based on workflow description and goal. "
                    "Uses advanced relevance scoring to suggest the best templates for your use case. "
                    "Returns templates with match scores and detailed information."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of the workflow you want to build"
                        },
                        "workflow_goal": {
                            "type": "string",
                            "description": "Optional: Specific goal or objective of the workflow"
                        },
                        "min_score": {
                            "type": "number",
                            "description": "Minimum relevance score (0.0-1.0, default: 0.3)",
                            "default": 0.3
                        },
                        "max_results": {
                            "type": "number",
                            "description": "Maximum number of recommendations (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["description"]
                }
            ),
            Tool(
                name="get_template_library",
                description=(
                    "📚 Get comprehensive template library report. "
                    "Shows all available templates grouped by category and difficulty, "
                    "with full descriptions, use cases, and metadata."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="search_templates",
                description=(
                    "🔍 Search templates by keyword or phrase. "
                    "Searches across template names, descriptions, tags, and use cases. "
                    "Great for finding templates when you know what you're looking for."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'email', 'database sync', 'notification')"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_templates_by_category",
                description=(
                    "📁 Get all templates in a specific category. "
                    "Categories: api, reporting, integration, communication, data_pipeline, "
                    "monitoring, notification, file_processing"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Category name",
                            "enum": ["api", "reporting", "integration", "communication",
                                   "data_pipeline", "monitoring", "notification", "file_processing"]
                        }
                    },
                    "required": ["category"]
                }
            ),
            Tool(
                name="get_templates_by_difficulty",
                description=(
                    "📊 Get templates filtered by difficulty level. "
                    "Helps find templates appropriate for your skill level."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "difficulty": {
                            "type": "string",
                            "description": "Difficulty level",
                            "enum": ["beginner", "intermediate", "advanced"]
                        }
                    },
                    "required": ["difficulty"]
                }
            ),
            Tool(
                name="get_template_details",
                description=(
                    "📄 Get detailed information about a specific template. "
                    "Shows full template structure, nodes, estimated time, and implementation guide."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "Template ID (e.g., 'api_endpoint', 'data_sync', 'email_automation')"
                        }
                    },
                    "required": ["template_id"]
                }
            ),
            Tool(
                name="add_node_intent",
                description="📝 Add 'why' metadata to a workflow node for AI context continuity. Helps LLMs remember reasoning, assumptions, and risks across iterations.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"node_name":{"type":"string","description":"Name of the node to add intent to"},"reason":{"type":"string","description":"Why this node exists / what problem it solves"},"assumption":{"type":"string","description":"Optional: Assumptions made when building this node"},"risk":{"type":"string","description":"Optional: Known risks or limitations"},"alternative":{"type":"string","description":"Optional: Alternative approaches considered"},"dependency":{"type":"string","description":"Optional: Dependencies on other nodes or systems"}},"required":["workflow_id","node_name","reason"]}
            ),
            Tool(
                name="get_workflow_intents",
                description="📋 Get all intent metadata from a workflow. Shows the 'why' behind each node - perfect for understanding existing workflows.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"format":{"type":"string","description":"Output format: 'report' (markdown) or 'json'","enum":["report","json"],"default":"report"}},"required":["workflow_id"]}
            ),
            Tool(
                name="analyze_intent_coverage",
                description="📊 Analyze how well a workflow is documented with intent metadata. Shows coverage percentage and recommendations.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to analyze"}},"required":["workflow_id"]}
            ),
            Tool(
                name="suggest_node_intent",
                description="💡 Get AI-generated intent template for a specific node. Provides a starting point for documenting the 'why'.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"node_name":{"type":"string","description":"Node name to generate suggestion for"}},"required":["workflow_id","node_name"]}
            ),
            Tool(
                name="update_node_intent",
                description="✏️ Update existing intent metadata for a node. Refine documentation as understanding evolves.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string"},"node_name":{"type":"string"},"reason":{"type":"string"},"assumption":{"type":"string"},"risk":{"type":"string"},"alternative":{"type":"string"},"dependency":{"type":"string"}},"required":["workflow_id","node_name"]}
            ),
            Tool(
                name="remove_node_intent",
                description="🗑️ Remove intent metadata from a node. Use when intent needs to be completely rewritten.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"node_name":{"type":"string","description":"Node name to remove intent from"}},"required":["workflow_id","node_name"]}
            ),
            Tool(
                name="watch_workflow_execution",
                description="👁️ Monitor workflow execution and get detailed error feedback. Returns execution status with error analysis if execution failed.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to monitor"},"execution_id":{"type":"string","description":"Optional: Specific execution ID. If not provided, analyzes the most recent execution."}},"required":["workflow_id"]}
            ),
            Tool(
                name="get_execution_error_context",
                description="🔍 Get detailed error context for a failed execution. Extracts error node, simplifies error message, provides fix suggestions.",
                inputSchema={"type":"object","properties":{"execution_id":{"type":"string","description":"Execution ID that failed"},"workflow_id":{"type":"string","description":"Workflow ID"}},"required":["execution_id","workflow_id"]}
            ),
            Tool(
                name="analyze_execution_errors",
                description="📊 Analyze error patterns across multiple executions of a workflow. Identifies common failure points and recurring issues.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to analyze"},"limit":{"type":"number","description":"Number of recent executions to analyze (default: 10)","default":10}},"required":["workflow_id"]}
            ),
            Tool(
                name="detect_workflow_drift",
                description="🔍 Detect workflow degradation over time by comparing baseline vs current execution patterns. Identifies success rate drops, performance degradation, and new error patterns.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to analyze"},"lookback_days":{"type":"number","description":"Days of history to analyze (default: 30)","default":30}},"required":["workflow_id"]}
            ),
            Tool(
                name="analyze_drift_pattern",
                description="🔬 Deep analysis of a specific drift pattern. Finds when drift started, whether it was gradual, and potential causes.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"pattern_type":{"type":"string","description":"Pattern type: success_rate_drift, performance_drift, new_error_pattern, error_frequency_drift"}},"required":["workflow_id","pattern_type"]}
            ),
            Tool(
                name="get_drift_root_cause",
                description="🎯 Determine root cause of detected drift. Analyzes patterns and provides evidence-based root cause with confidence score.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"lookback_days":{"type":"number","description":"Days of history (default: 30)","default":30}},"required":["workflow_id"]}
            ),
            Tool(
                name="get_drift_fix_suggestions",
                description="💡 Get actionable fix suggestions for detected drift. Provides specific changes to apply, with confidence scores and testing recommendations.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"}},"required":["workflow_id"]}
            ),
            Tool(
                name="detect_schema_drift",
                description="📋 Detect API schema changes: missing fields, type changes, structure changes. Identifies breaking API changes before they cause failures.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to analyze"},"lookback_days":{"type":"number","description":"Days of history to analyze (default: 30)","default":30}},"required":["workflow_id"]}
            ),
            Tool(
                name="detect_rate_limit_drift",
                description="⏱️ Detect rate limit issues: 429 errors, quota proximity, throughput degradation. Identifies when workflows are hitting API limits.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to analyze"},"lookback_days":{"type":"number","description":"Days of history to analyze (default: 30)","default":30}},"required":["workflow_id"]}
            ),
            Tool(
                name="detect_quality_drift",
                description="📊 Detect data quality degradation: empty values, format violations, completeness issues. Identifies when data quality is declining.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to analyze"},"lookback_days":{"type":"number","description":"Days of history to analyze (default: 30)","default":30}},"required":["workflow_id"]}
            ),
            Tool(
                name="explain_workflow",
                description="📖 Generate comprehensive workflow explanation: purpose, data flow, dependencies, risks. Perfect for audit, onboarding, and documentation.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID to explain"},"format":{"type":"string","description":"Output format: markdown, json, or text (default: markdown)","default":"markdown"},"include_analysis":{"type":"boolean","description":"Include semantic analysis and execution history (default: true)","default":True}},"required":["workflow_id"]}
            ),
            Tool(
                name="get_workflow_purpose",
                description="🎯 Quick analysis of workflow purpose and business domain. Identifies what the workflow does and why it exists.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"}},"required":["workflow_id"]}
            ),
            Tool(
                name="trace_data_flow",
                description="🔄 Trace data movement through workflow: sources, transformations, destinations. Identifies critical data paths.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"}},"required":["workflow_id"]}
            ),
            Tool(
                name="map_dependencies",
                description="🔗 Map all workflow dependencies: internal workflows, external services, credentials. Identifies single points of failure.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"}},"required":["workflow_id"]}
            ),
            Tool(
                name="analyze_workflow_risks",
                description="⚠️ Comprehensive risk assessment: data loss, security, performance, availability, compliance risks with mitigation plan.",
                inputSchema={"type":"object","properties":{"workflow_id":{"type":"string","description":"Workflow ID"},"include_analysis":{"type":"boolean","description":"Include semantic analysis and execution history (default: true)","default":True}},"required":["workflow_id"]}
            ),
            Tool(
                name="simulate_workflow_changes",
                description="🔮 Terraform-style change preview: compare old vs new workflow, analyze impact, detect breaking changes. Shows color-coded diff with recommendations.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "workflow_id":{"type":"string","description":"Current workflow ID"},
                        "new_workflow":{"type":"object","description":"New workflow JSON structure"}
                    },
                    "required":["workflow_id","new_workflow"]
                }
            ),
            Tool(
                name="compare_workflows",
                description="📊 Side-by-side workflow comparison: detailed diff of nodes, connections, settings. Identifies added/removed/modified elements.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "workflow_id_1":{"type":"string","description":"First workflow ID"},
                        "workflow_id_2":{"type":"string","description":"Second workflow ID"}
                    },
                    "required":["workflow_id_1","workflow_id_2"]
                }
            ),
            Tool(
                name="analyze_change_impact",
                description="⚡ Multi-dimensional impact analysis: data flow, execution, dependencies, triggers, downstream workflows. Calculates overall risk score (0-10).",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "workflow_id":{"type":"string","description":"Current workflow ID"},
                        "new_workflow":{"type":"object","description":"Proposed workflow changes"},
                        "include_downstream":{"type":"boolean","description":"Check impact on workflows that call this one","default":True}
                    },
                    "required":["workflow_id","new_workflow"]
                }
            ),
            Tool(
                name="create_change_request",
                description="📝 Create change request for approval workflow: documents changes, requester, reason. Returns request ID for tracking.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "workflow_id":{"type":"string","description":"Workflow ID"},
                        "workflow_name":{"type":"string","description":"Workflow name"},
                        "changes":{"type":"object","description":"Proposed changes"},
                        "reason":{"type":"string","description":"Why this change is needed"},
                        "requester":{"type":"string","description":"Person requesting change"}
                    },
                    "required":["workflow_id","workflow_name","changes","reason","requester"]
                }
            ),
            Tool(
                name="review_change_request",
                description="✅ Approve or reject change request: adds reviewer, comments, updates status.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "request_id":{"type":"string","description":"Change request ID"},
                        "action":{"type":"string","enum":["approve","reject"],"description":"Review decision"},
                        "reviewer":{"type":"string","description":"Person reviewing"},
                        "comments":{"type":"string","description":"Review comments/reason"}
                    },
                    "required":["request_id","action","reviewer"]
                }
            ),
            Tool(
                name="get_change_history",
                description="📜 Get change request history for workflow: all past changes, approvals, rejections with timestamps.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "workflow_id":{"type":"string","description":"Workflow ID"}
                    },
                    "required":["workflow_id"]
                }
            ),
            Tool(
                name="find_templates_by_intent",
                description="🎯 Smart template matching: Describe your goal → get template suggestions with match explanation. Uses intent-based semantic matching.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "description":{"type":"string","description":"Natural language description of what you want to build"},
                        "top_k":{"type":"integer","description":"Number of suggestions (default: 5)","default":5}
                    },
                    "required":["description"]
                }
            ),
            Tool(
                name="extract_template_intent",
                description="🧠 Extract template intent: purpose, assumptions, risks, data flow, external systems. Makes templates 'thinkable'.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "template_id":{"type":"string","description":"Template ID"}
                    },
                    "required":["template_id"]
                }
            ),
            Tool(
                name="adapt_template",
                description="🔧 Adapt template for production: replace placeholders, abstract credentials, modernize deprecated nodes, add error handling.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "template_id":{"type":"string","description":"Template ID"},
                        "replacements":{"type":"object","description":"Placeholder replacements {\"API_URL\": \"https://...\"}"},
                        "add_error_handling":{"type":"boolean","description":"Add error handling (default: true)","default":True},
                        "modernize_nodes":{"type":"boolean","description":"Replace deprecated nodes (default: true)","default":True}
                    },
                    "required":["template_id"]
                }
            ),
            Tool(
                name="get_template_provenance",
                description="📊 Get template provenance: source, author, success rate, usage stats, trust score. Shows template reliability.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "template_id":{"type":"string","description":"Template ID"}
                    },
                    "required":["template_id"]
                }
            ),
            Tool(
                name="get_template_requirements",
                description="📋 Get template requirements: placeholders to fill, credentials needed, external systems. Pre-deployment checklist.",
                inputSchema={
                    "type":"object",
                    "properties":{
                        "template_id":{"type":"string","description":"Template ID"}
                    },
                    "required":["template_id"]
                }
            ),
            # Migration & Compatibility Tools
            Tool(
                name="check_workflow_compatibility",
                description=(
                    "🔍 Check workflow for node compatibility issues with current n8n version. "
                    "Detects deprecated parameters, breaking changes, and outdated node versions. "
                    "Essential before deploying old workflows or community templates."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to check"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="migrate_workflow",
                description=(
                    "🔄 Automatically migrate workflow to latest node versions. "
                    "Applies migration rules to update deprecated parameters, fix breaking changes, "
                    "and upgrade node versions. Includes dry-run mode for preview."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to migrate"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "If true, preview changes without applying (default: false)",
                            "default": False
                        },
                        "target_version": {
                            "type": "number",
                            "description": "Optional: Target node version (defaults to latest)"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="get_migration_preview",
                description=(
                    "👁️ Preview what would change if workflow is migrated. "
                    "Shows detailed diff of node versions, parameter changes, and migration steps. "
                    "Use before migrating to understand impact."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to preview"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="batch_check_compatibility",
                description=(
                    "📊 Batch check compatibility for multiple workflows. "
                    "Scans all workflows (or filtered list) for compatibility issues. "
                    "Perfect for auditing entire n8n instance after version upgrade."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional: Specific workflow IDs (if not provided, checks all)"
                        }
                    }
                }
            ),
            Tool(
                name="get_available_migrations",
                description=(
                    "📋 List available migration rules for a node type. "
                    "Shows what migrations are available, from/to versions, and severity. "
                    "Useful for understanding what can be auto-migrated."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "string",
                            "description": "Node type (e.g., 'n8n-nodes-base.httpRequest')"
                        }
                    },
                    "required": ["node_type"]
                }
            ),
            # Template Management Tools
            Tool(
                name="sync_templates",
                description=(
                    "🔄 Sync templates from remote sources. "
                    "Downloads and caches templates from n8n official, GitHub, or community sources. "
                    "Uses smart 24-hour caching to minimize API calls. Use force=true to force refresh."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "enum": ["all", "n8n_official", "github", "community"],
                            "description": "Source to sync from",
                            "default": "all"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force sync even if recently synced (ignores 24h cache)",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="search_templates",
                description=(
                    "🔍 Search workflow templates with advanced filters. "
                    "Full-text search using SQLite FTS5 for fast results. "
                    "Filter by query text, category, tags, node types, or source. "
                    "Returns template metadata including complexity, nodes used, and setup time."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Full-text search query (searches name, description, tags)"
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category (e.g., 'api', 'data_pipeline', 'communication')"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags (matches templates with any of these tags)"
                        },
                        "node_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by node types used (e.g., ['webhook', 'http_request'])"
                        },
                        "source": {
                            "type": "string",
                            "enum": ["n8n_official", "github", "community"],
                            "description": "Filter by template source"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results to return",
                            "default": 20
                        }
                    }
                }
            ),
            Tool(
                name="get_template_stats",
                description=(
                    "📊 Get statistics about cached templates. "
                    "Shows total count, templates by source, top categories, popular tags, "
                    "frequently used nodes, and sync status for all sources."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_popular_templates",
                description=(
                    "⭐ Get most popular templates by view count. "
                    "Returns templates sorted by popularity from the n8n community."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max templates to return",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="get_recent_templates",
                description=(
                    "🆕 Get most recently added templates. "
                    "Returns latest templates sorted by creation date."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max templates to return",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="get_template_by_id",
                description=(
                    "📄 Get specific template by ID. "
                    "Returns full template data including nodes, connections, and metadata."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "Template identifier"
                        }
                    },
                    "required": ["template_id"]
                }
            ),
            Tool(
                name="clear_template_cache",
                description=(
                    "🗑️ Clear template cache. "
                    "Removes cached templates for a specific source or all sources. "
                    "Use this if you want to force a fresh sync."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "enum": ["all", "n8n_official", "github", "community"],
                            "description": "Source to clear, or 'all' for everything",
                            "default": "all"
                        }
                    }
                }
            ),
            # GitHub Integration Tools
            Tool(
                name="discover_github_templates",
                description=(
                    "🐙 Discover n8n workflow templates in GitHub repositories. "
                    "Searches GitHub for repositories containing n8n workflows using GitHub Search API. "
                    "Returns repository metadata including stars, description, topics, and last update. "
                    "Use this to find community-created workflow templates before importing them."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'n8n automation', 'n8n workflows')",
                            "default": "n8n workflows"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max repositories to return",
                            "default": 10
                        }
                    }
                }
            ),
            Tool(
                name="import_github_repo",
                description=(
                    "📦 Import n8n workflow templates from a GitHub repository. "
                    "Fetches all n8n workflow JSON files from the specified repository. "
                    "Searches common paths like '.n8n/workflows/', 'workflows/', etc. "
                    "Validates workflows, extracts metadata, and caches them locally. "
                    "Optionally adds the repo to the sync list for regular updates."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_full_name": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo' (e.g., 'n8n-io/n8n-docs')"
                        },
                        "add_to_sync": {
                            "type": "boolean",
                            "description": "Add repository to regular sync list",
                            "default": True
                        }
                    },
                    "required": ["repo_full_name"]
                }
            ),
            # Intent-Based Search Tools
            Tool(
                name="search_templates_by_intent",
                description=(
                    "🎯 Search templates using intent-based semantic matching. "
                    "Goes beyond keyword search to understand what you're trying to build. "
                    "Extracts intent (goal, triggers, actions, nodes needed) from your natural language query. "
                    "Scores templates using multi-dimensional similarity: goal (30%), nodes (25%), triggers (15%), actions (15%), domain (10%), complexity (5%). "
                    "Returns ranked results with match percentage and explanation."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language description of what you want to build (e.g., 'I need to automatically respond to customer emails with AI')"
                        },
                        "min_score": {
                            "type": "number",
                            "description": "Minimum match score (0.0-1.0)",
                            "default": 0.3
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results to return",
                            "default": 20
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="explain_template_match",
                description=(
                    "📊 Explain why a template matches your query. "
                    "Provides detailed breakdown of intent similarity scoring. "
                    "Shows scores for goal similarity, node overlap, trigger match, action match, domain match, and complexity match. "
                    "Helps understand why certain templates were recommended."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Your original search query"
                        },
                        "template_id": {
                            "type": "string",
                            "description": "Template ID to explain"
                        }
                    },
                    "required": ["query", "template_id"]
                }
            ),
            # Security Audit & Governance Tools
            Tool(
                name="audit_workflow_security",
                description=(
                    "🔐 Run comprehensive security audit on a workflow. "
                    "Detects hardcoded secrets (API keys, passwords, tokens), "
                    "missing authentication, insecure webhooks, data exposure risks. "
                    "Returns security score (0-100), risk level, and detailed findings. "
                    "Enterprise-grade security auditing for compliance and governance."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to audit"
                        },
                        "format": {
                            "type": "string",
                            "description": "Report format (markdown, json, text)",
                            "enum": ["markdown", "json", "text"],
                            "default": "markdown"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="get_security_summary",
                description=(
                    "📊 Get concise security summary for a workflow. "
                    "Quick overview of security score, risk level, and findings count. "
                    "Useful for dashboards and quick checks."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="check_compliance",
                description=(
                    "✅ Check if workflow meets security compliance standards. "
                    "Standards: basic (no critical findings), strict (no critical/high), "
                    "enterprise (score >= 85, no critical/high, authenticated webhooks). "
                    "Returns compliance status and violations list."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID"
                        },
                        "standard": {
                            "type": "string",
                            "description": "Compliance standard",
                            "enum": ["basic", "strict", "enterprise"],
                            "default": "basic"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="get_critical_findings",
                description=(
                    "🚨 Get only critical and high severity security findings. "
                    "Filters out low/medium issues for quick triage. "
                    "Returns secrets, authentication, and exposure issues."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="detect_workflow_drift",
                description=(
                    "📊 Detect workflow drift and degradation over time. "
                    "Analyzes execution history to detect: success rate drops, "
                    "performance degradation, new error patterns, API changes, "
                    "rate limit issues, schema drift, and data quality issues. "
                    "Provides root cause analysis and fix suggestions. "
                    "Requires at least 10+ executions for accurate analysis."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to analyze"
                        },
                        "min_executions": {
                            "type": "integer",
                            "description": "Minimum executions to analyze (default: 20)",
                            "default": 20
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="analyze_drift_pattern",
                description=(
                    "🔬 Deep analysis of a specific drift pattern. "
                    "Takes a drift pattern and provides detailed insights, "
                    "change point detection, potential causes, and recommendations."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID"
                        },
                        "pattern_type": {
                            "type": "string",
                            "description": "Pattern type to analyze",
                            "enum": ["success_rate_drift", "performance_drift", "new_error_pattern", "error_frequency_drift"]
                        }
                    },
                    "required": ["workflow_id", "pattern_type"]
                }
            ),
            Tool(
                name="get_drift_fix_suggestions",
                description=(
                    "🔧 Get fix suggestions for detected drift issues. "
                    "Provides actionable recommendations based on root cause analysis. "
                    "Includes node-specific fixes, configuration changes, and best practices."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID"
                        }
                    },
                    "required": ["workflow_id"]
                }
            ),
            Tool(
                name="discover_nodes",
                description=(
                    "📦 Discover node types by analyzing existing workflows. "
                    "Learns from your workflows to find which nodes are available and used. "
                    "Returns discovered nodes with usage statistics and popularity. "
                    "Run this periodically to update node knowledge."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_node_schema",
                description=(
                    "🔍 Get discovered schema for a specific node type. "
                    "Returns parameters, credentials, and examples learned from workflows. "
                    "Shows which parameters are used in practice and their types. "
                    "Includes real-world usage examples from your workflows."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "string",
                            "description": "Node type name (e.g., 'n8n-nodes-base.googleDrive', 'n8n-nodes-base.slack')"
                        }
                    },
                    "required": ["node_type"]
                }
            ),
            Tool(
                name="search_nodes",
                description=(
                    "🔎 Search discovered nodes by keyword. "
                    "Find nodes related to specific services or functionality. "
                    "Results sorted by popularity (usage count)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'google', 'database', 'slack')"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="recommend_nodes_for_task",
                description=(
                    "💡 Get node recommendations for a specific task. "
                    "Uses workflow-learned patterns to suggest appropriate nodes. "
                    "Considers node popularity and relevance to your task description."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "What you want to accomplish (e.g., 'send slack message', 'query database')"
                        }
                    },
                    "required": ["task_description"]
                }
            ),
            Tool(
                name="get_node_documentation",
                description=(
                    "📖 Get official n8n documentation for a specific node. "
                    "Fetches and displays the official documentation from docs.n8n.io. "
                    "Supports core nodes (code, http, webhook) and app nodes (googleSheets, slack, telegram)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "string",
                            "description": "Node type to get documentation for (e.g., 'code', 'n8n-nodes-base.http', 'googleSheets')"
                        }
                    },
                    "required": ["node_type"]
                }
            ),
            Tool(
                name="search_n8n_docs",
                description=(
                    "🔍 Search n8n official documentation. "
                    "Finds relevant documentation pages for your query. "
                    "Returns URLs to core nodes, app nodes, and documentation sections."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to search for (e.g., 'webhook', 'error handling', 'expressions')"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls by routing to appropriate handler"""
        nonlocal node_recommender
        
        try:
            # Define tool name sets for each handler
            workflow_tool_names = {
                "suggest_workflow_nodes", "generate_workflow_template", "analyze_workflow",
                "list_workflows", "create_workflow", "update_workflow", "delete_workflow",
                "get_workflow", "get_workflow_details", "activate_workflow", "deactivate_workflow",
                "get_workflow_executions", "execute_workflow", "validate_workflow_structure",
                "get_workflow_statistics", "clone_workflow"
            }
            
            security_tool_names = {
                "audit_workflow_security", "get_security_summary", "check_compliance", 
                "get_critical_findings", "rbac_get_status", "rbac_add_user", 
                "rbac_get_user_info", "rbac_check_permission", "rbac_create_approval_request",
                "rbac_approve_request", "rbac_reject_request", "rbac_get_pending_approvals",
                "rbac_create_tenant", "rbac_get_audit_log"
            }
            
            template_tool_names = {
                "recommend_templates", "get_template_library", "search_templates",
                "get_templates_by_category", "get_templates_by_difficulty", "get_template_details",
                "analyze_intent_coverage", "suggest_node_intent", "add_node_intent",
                "get_workflow_intents", "update_node_intent"
            }
            
            execution_tool_names = {
                "get_executions", "get_execution_details", "watch_workflow_execution",
                "get_execution_error_context", "analyze_execution_errors"
            }
            
            drift_tool_names = {
                "detect_workflow_drift", "analyze_drift_pattern", "get_drift_root_cause",
                "get_drift_fix_suggestions", "compare_workflows"
            }
            
            explainability_tool_names = {
                "explain_node", "explain_workflow", "get_workflow_purpose",
                "explain_template_match"
            }
            
            session_tool_names = {
                "get_session_state", "set_active_workflow", "get_active_workflow",
                "get_recent_workflows", "get_session_history", "clear_session_state"
            }
            
            migration_tool_names = {
                "migrate_workflow", "get_migration_preview", "batch_check_compatibility"
            }
            
            change_impact_tool_names = {
                "compare_workflows", "analyze_change_impact", "discover_nodes", "get_node_schema"
            }
            
            documentation_tool_names = {
                "get_node_documentation", "search_n8n_docs", "discover_github_templates", "import_github_repo"
            }
            
            advanced_template_tool_names = {
                "sync_templates", "get_template_stats", "get_popular_templates", "get_recent_templates",
                "get_template_by_id", "clear_template_cache", "find_templates_by_intent",
                "extract_template_intent", "adapt_template", "get_template_provenance",
                "get_template_requirements", "check_workflow_compatibility"
            }
            
            miscellaneous_tool_names = {
                "get_drift_root_cause", "get_drift_fix_suggestions", "detect_schema_drift",
                "detect_rate_limit_drift", "detect_quality_drift", "trace_data_flow",
                "map_dependencies", "simulate_workflow_changes", "create_change_request",
                "review_change_request", "get_change_history", "get_available_migrations",
                "generate_workflow_template", "debug_workflow_error", "search_nodes",
                "recommend_nodes_for_task"
            }
            
            validation_tool_names = {
                "validate_workflow", "validate_workflow_json", "analyze_workflow_semantics"
            }
            
            # Route to appropriate handler
            if name in workflow_tool_names:
                return await workflow_tools.handle(name, arguments)
            elif name in security_tool_names:
                return await security_tools.handle(name, arguments)
            elif name in template_tool_names:
                return await template_tools.handle(name, arguments)
            elif name in execution_tool_names:
                return await execution_tools.handle(name, arguments)
            elif name in drift_tool_names:
                return await drift_tools.handle(name, arguments)
            elif name in explainability_tool_names:
                return await explainability_tools.handle(name, arguments)
            elif name in session_tool_names:
                return await session_tools.handle(name, arguments)
            elif name in migration_tool_names:
                return await migration_tools.handle(name, arguments)
            elif name in change_impact_tool_names:
                return await change_impact_tools.handle(name, arguments)
            elif name in documentation_tool_names:
                return await documentation_tools.handle(name, arguments)
            elif name in advanced_template_tool_names:
                return await advanced_template_tools.handle(name, arguments)
            elif name in miscellaneous_tool_names:
                return await miscellaneous_tools.handle(name, arguments)
            elif name in validation_tool_names:
                return await validation_tools.handle(name, arguments)
            else:
                # Unknown tool
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            import traceback
            logger.error(f"Error in tool {name}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return [TextContent(type="text", text=f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}")]


    return server


async def main():
    """Main entry point"""
    import sys

    # Get configuration from environment
    api_url = os.getenv("N8N_API_URL")
    api_key = os.getenv("N8N_API_KEY")

    if not api_url or not api_key:
        logger.error("N8N_API_URL and N8N_API_KEY environment variables must be set")
        sys.exit(1)

    logger.info(f"Starting n8n Workflow Builder MCP Server... (API: {api_url})")

    try:
        server = create_n8n_server(api_url, api_key)
        logger.info("Server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Run the server
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
