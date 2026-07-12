# Policy Engine

Policy engine outputs:

- `allow`
- `deny`
- `requires_approval`

Current baseline behavior:

- Deny actions outside simulation boundary.
- Require approval for simulated user-impacting actions.
- Allow analysis-only actions.

Implementation:

`intent_fabric.policies.engine.PolicyEngine`
