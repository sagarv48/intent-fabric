"""MCP-style tools for intent planning and simulation."""

from __future__ import annotations

from typing import Any

from intent_fabric.approvals import ApprovalPackageGenerator
from intent_fabric.mcp.schema import envelope, unwrap_payload
from intent_fabric.policies import PolicyEngine
from intent_fabric.planning import RuleBasedPlanner, build_planner
from intent_fabric.serde import (
    parse_evidence_package_reference,
    parse_intent_request,
    parse_plan,
    parse_policy_decision,
    to_dict,
)
from intent_fabric.simulation import SimulationExecutor


class IntentFabricMCPTools:
    """Phase 2 MCP tool implementations."""

    def __init__(
        self,
        *,
        planner: RuleBasedPlanner | None = None,
        policy_engine: PolicyEngine | None = None,
        approval_generator: ApprovalPackageGenerator | None = None,
        simulator: SimulationExecutor | None = None,
    ) -> None:
        self._planner = planner or build_planner() or RuleBasedPlanner()
        self._policy_engine = policy_engine or PolicyEngine()
        self._approval_generator = approval_generator or ApprovalPackageGenerator()
        self._simulator = simulator or SimulationExecutor()

    def create_plan_from_evidence(
        self,
        intent_request: dict[str, object],
        evidence_package: dict[str, object],
    ) -> dict[str, Any]:
        intent = parse_intent_request(intent_request)
        evidence = parse_evidence_package_reference(evidence_package)
        plan = self._planner.create_plan(intent, evidence)
        return envelope(tool="create_plan_from_evidence", payload=to_dict(plan))

    def validate_plan(self, plan: dict[str, object]) -> dict[str, Any]:
        parsed_plan = parse_plan(unwrap_payload(plan))  # type: ignore[arg-type]
        decision = self._policy_engine.evaluate(parsed_plan)
        return envelope(tool="validate_plan", payload=to_dict(decision))

    def create_approval_package(
        self,
        plan: dict[str, object],
        policy_decision: dict[str, object],
        requested_by: str = "system",
    ) -> dict[str, Any]:
        parsed_plan = parse_plan(unwrap_payload(plan))  # type: ignore[arg-type]
        parsed_decision = parse_policy_decision(unwrap_payload(policy_decision))  # type: ignore[arg-type]
        approval_request = self._approval_generator.create(
            plan=parsed_plan,
            decision=parsed_decision,
            requested_by=requested_by,
        )
        return envelope(tool="create_approval_package", payload=to_dict(approval_request))

    def simulate_plan(
        self,
        plan: dict[str, object],
        policy_decision: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        parsed_plan = parse_plan(unwrap_payload(plan))  # type: ignore[arg-type]
        if policy_decision is None:
            parsed_decision = self._policy_engine.evaluate(parsed_plan)
        else:
            parsed_decision = parse_policy_decision(unwrap_payload(policy_decision))  # type: ignore[arg-type]
        result = self._simulator.simulate(plan=parsed_plan, decision=parsed_decision)
        return envelope(tool="simulate_plan", payload=to_dict(result))
