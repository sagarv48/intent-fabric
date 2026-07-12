from __future__ import annotations

from intent_fabric.models import EvidenceItemReference, EvidencePackageReference, IntentRequest
from intent_fabric.planning import RuleBasedPlanner


def test_rule_based_planner_creates_structured_plan() -> None:
    planner = RuleBasedPlanner()
    intent = IntentRequest(
        intent_id="intent_2",
        user_request="Update a document and send notification",
        requested_actions=["document_update", "notification_send"],
    )
    evidence = EvidencePackageReference(
        query_text="documentation standards",
        items=[
            EvidenceItemReference(
                chunk_id=10,
                document_uri="memory://doc-10",
                snippet="Document updates should be reviewed.",
                score=0.8,
            )
        ],
    )

    plan = planner.create_plan(intent, evidence)
    assert plan.intent_id == intent.intent_id
    assert len(plan.steps) == 2
    assert all(step.action_contract.simulated for step in plan.steps)
