from __future__ import annotations

import json
from pathlib import Path

from intent_fabric.mcp import MCP_SCHEMA_VERSION
from intent_fabric.mcp import IntentFabricMCPTools


def _load_fixture(name: str) -> dict[str, object]:
    path = Path(__file__).parent / "fixtures" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixture_based_end_to_end_flow() -> None:
    tools = IntentFabricMCPTools()
    intent = _load_fixture("intent_request.json")
    evidence = _load_fixture("evidence_package.json")

    plan = tools.create_plan_from_evidence(intent_request=intent, evidence_package=evidence)
    decision = tools.validate_plan(plan)
    approval = tools.create_approval_package(plan, decision, requested_by="integration-test")
    simulation = tools.simulate_plan(plan, decision)

    assert plan["schema_version"] == MCP_SCHEMA_VERSION
    assert plan["tool"] == "create_plan_from_evidence"
    assert isinstance(plan["payload"]["steps"], list)

    assert decision["schema_version"] == MCP_SCHEMA_VERSION
    assert decision["tool"] == "validate_plan"
    assert decision["payload"]["decision"] in {"allow", "requires_approval", "deny"}

    assert approval["schema_version"] == MCP_SCHEMA_VERSION
    assert approval["tool"] == "create_approval_package"
    assert approval["payload"]["plan_id"] == plan["payload"]["plan_id"]

    assert simulation["schema_version"] == MCP_SCHEMA_VERSION
    assert simulation["tool"] == "simulate_plan"
    assert simulation["payload"]["no_external_side_effects"] is True
