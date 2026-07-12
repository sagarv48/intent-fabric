from __future__ import annotations

from intent_fabric.mcp import MCP_SCHEMA_VERSION
from intent_fabric.mcp import IntentFabricMCPTools


def test_mcp_tools_end_to_end() -> None:
    tools = IntentFabricMCPTools()
    plan = tools.create_plan_from_evidence(
        intent_request={
            "intent_id": "intent_1",
            "user_request": "Create a ticket and notify stakeholders",
            "requested_actions": ["ticket_create", "notification_send"],
        },
        evidence_package={
            "query_text": "incident handling",
            "items": [
                {
                    "chunk_id": 1,
                    "document_uri": "memory://doc",
                    "snippet": "Use issue tracking for incidents.",
                    "score": 0.9,
                }
            ],
        },
    )
    decision = tools.validate_plan(plan)
    approval = tools.create_approval_package(plan, decision, requested_by="user")
    simulation = tools.simulate_plan(plan, decision)

    assert plan["schema_version"] == MCP_SCHEMA_VERSION
    assert plan["payload"]["intent_id"] == "intent_1"
    assert decision["payload"]["decision"] in {"allow", "requires_approval", "deny"}
    assert approval["payload"]["plan_id"] == plan["payload"]["plan_id"]
    assert simulation["payload"]["no_external_side_effects"] is True
