# Intent Fabric

Intent Fabric is a vendor-neutral planning and approval framework.

In simple terms: it takes **intent + evidence** and turns it into a **safe, reviewable plan**. It does not execute real-world actions.

If Knowledge Fabric answers _"what evidence is relevant?"_, Intent Fabric answers _"what should we do next, safely?"_.

## What it does

- Converts intent + evidence into deterministic plans
- Produces action contracts for each plan step
- Validates plans with a policy engine (`allow`, `deny`, `requires_approval`)
- Generates approval packages for review workflows
- Simulates execution with zero external side effects
- Exposes MCP-style planning tools

## Why this exists

Teams often jump from user request straight to action. Intent Fabric adds a policy-aware middle layer so actions are:

- explicit,
- auditable,
- reviewable before execution.

## Core flow

```text
Intent Request
  ->
Evidence Package Reference
  ->
Rule-Based Planner
  ->
Policy Decision
  ->
Approval Package (if needed)
  ->
Simulation Result
```

## Quick start

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

Pinned development dependencies are listed in `requirements-dev.txt`.

## Minimal usage example

```python
from intent_fabric.mcp import IntentFabricMCPTools

tools = IntentFabricMCPTools()

plan = tools.create_plan_from_evidence(
    intent_request={
        "intent_id": "intent_1",
        "user_request": "Create a ticket and notify stakeholders",
        "requested_actions": ["ticket_create", "notification_send"],
    },
    evidence_package={
        "query_text": "incident handling guidance",
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
approval = tools.create_approval_package(plan, decision, requested_by="analyst")
simulation = tools.simulate_plan(plan, decision)
```

## MCP tools

- `create_plan_from_evidence`
- `validate_plan`
- `create_approval_package`
- `simulate_plan`

## What this is not

- Not a runtime connector
- Not a workflow execution engine
- Not a product-specific integration layer

## Phase boundaries

- This repository is **Phase 2** only.
- Real execution and runtime connectors belong to **Phase 3 enterprise adapters**.
- No product-specific integration is included.

## Versioning and releases

- Changelog: `CHANGELOG.md`
- Release guide: `docs/release-process.md`
