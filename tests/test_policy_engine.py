from __future__ import annotations

from intent_fabric.models import ActionContract, Plan, PlanStep, PolicyDecisionType
from intent_fabric.policies import PolicyEngine


def _plan_with_action(action_type: str) -> Plan:
    return Plan(
        plan_id="plan_1",
        intent_id="intent_1",
        summary="test",
        steps=[
            PlanStep(
                step_id="step_1",
                title="step",
                description="desc",
                action_contract=ActionContract(
                    contract_id="contract_1",
                    action_type=action_type,
                    target="artifact",
                    intent="intent",
                    simulated=True,
                    parameters={},
                    justification="rule",
                ),
            )
        ],
    )


def test_policy_allow() -> None:
    engine = PolicyEngine()
    decision = engine.evaluate(_plan_with_action("analysis_review"))
    assert decision.decision is PolicyDecisionType.ALLOW
    assert decision.requires_approval is False


def test_policy_requires_approval() -> None:
    engine = PolicyEngine()
    decision = engine.evaluate(_plan_with_action("ticket_create"))
    assert decision.decision is PolicyDecisionType.REQUIRES_APPROVAL
    assert decision.requires_approval is True


def test_policy_deny() -> None:
    engine = PolicyEngine()
    decision = engine.evaluate(_plan_with_action("runtime_connector"))
    assert decision.decision is PolicyDecisionType.DENY
    assert decision.requires_approval is False
