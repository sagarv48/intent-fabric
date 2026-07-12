"""Policy engine for plan validation."""

from __future__ import annotations

from intent_fabric.models import Plan, PolicyDecision, PolicyDecisionType

_DENY_ACTION_TYPES = {"runtime_connector", "external_write"}
_REQUIRES_APPROVAL_ACTION_TYPES = {"ticket_create", "document_update", "notification_send"}


class PolicyEngine:
    """Applies simple allow/deny/requires_approval rules to a plan."""

    def evaluate(self, plan: Plan) -> PolicyDecision:
        reasons: list[str] = []
        action_types = [step.action_contract.action_type for step in plan.steps]

        if any(action in _DENY_ACTION_TYPES for action in action_types):
            reasons.append("Plan contains action types outside simulation boundary.")
            return PolicyDecision(
                plan_id=plan.plan_id,
                decision=PolicyDecisionType.DENY,
                reasons=reasons,
                requires_approval=False,
            )

        if any(action in _REQUIRES_APPROVAL_ACTION_TYPES for action in action_types):
            reasons.append("Plan contains simulated user-impacting actions that require approval.")
            return PolicyDecision(
                plan_id=plan.plan_id,
                decision=PolicyDecisionType.REQUIRES_APPROVAL,
                reasons=reasons,
                requires_approval=True,
            )

        reasons.append("Plan is within simulation-only policy boundaries.")
        return PolicyDecision(
            plan_id=plan.plan_id,
            decision=PolicyDecisionType.ALLOW,
            reasons=reasons,
            requires_approval=False,
        )
