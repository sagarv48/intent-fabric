# Approval Model

Approval packages are generated when policy decision is `requires_approval`.

Approval request includes:

- approval id
- plan id
- summary
- requested by
- step ids
- policy reasons

Implementation:

`intent_fabric.approvals.generator.ApprovalPackageGenerator`
