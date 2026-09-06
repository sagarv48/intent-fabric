# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Intent Fabric governs autonomous action boundaries and approval safety. If you discover a vulnerability or potential policy engine bypass:

1. **Do not create a public issue.**
2. Report the vulnerability privately via GitHub Private Vulnerability Reporting or email `security@intent-fabric.dev`.
3. Include an example intent request, evidence package, and rule configuration demonstrating the issue.

We will acknowledge reports within 48 hours and coordinate a patch release.

---

## Deployment & Security Configuration Flags

To ensure security controls adapt cleanly to different enterprise deployment architectures without breaking operational velocity, Intent Fabric provides the following environment configuration toggles:

| Environment Variable | Default | Purpose & Flexibility |
| :--- | :--- | :--- |
| `FABRIC_SIGNING_KEY` | *(dev key)* | Secret key used to compute and verify HMAC-SHA256 signatures on approval decisions. In production, provide an air-gapped or KMS-managed secret. |
| `FABRIC_APPROVAL_ENFORCEMENT` | `enforce` | Set to `permissive` or `audit_only` in staging/testing environments to log warnings instead of blocking actions when testing unauthenticated pipelines. |
| `INTENT_STRICT_ACTION_VALIDATION` | `true` | When `true`, enforces safe action naming (`^[a-zA-Z0-9_.:-]{1,128}$`). Set to `false` if custom legacy action schemes are required. |
| `INTENT_ACTION_SYNTAX_REGEX` | *(unset)* | Custom regex string to define organization-specific action naming conventions. |

