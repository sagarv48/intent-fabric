"""Cryptographic signing and verification for human-in-the-loop approvals.

Prevents approval forgery, tampering in transit, and non-repudiation
of sensitive action authorization.
"""

from __future__ import annotations

import hmac
import hashlib
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime


_DEFAULT_DEV_KEY = "fabric-insecure-dev-hmac-key-change-in-production"


def get_signing_key(override_key: str | None = None) -> bytes:
    """Retrieve the HMAC signing key from parameter, environment, or default."""
    if override_key:
        return override_key.encode("utf-8")
    env_key = os.environ.get("FABRIC_SIGNING_KEY", "")
    if env_key:
        return env_key.encode("utf-8")
    return _DEFAULT_DEV_KEY.encode("utf-8")


def canonical_approval_payload(
    *,
    approval_id: str,
    plan_id: str,
    step_ids: list[str],
    decision: str,
    reviewer: str,
    timestamp: str,
) -> bytes:
    """Create a deterministic canonical byte string representing an approval decision."""
    sorted_steps = ",".join(sorted(step_ids))
    canonical_str = f"{approval_id}|{plan_id}|{sorted_steps}|{decision.strip().lower()}|{reviewer.strip()}|{timestamp.strip()}"
    return canonical_str.encode("utf-8")


def compute_approval_signature(
    *,
    approval_id: str,
    plan_id: str,
    step_ids: list[str],
    decision: str,
    reviewer: str,
    timestamp: str,
    secret_key: str | None = None,
) -> str:
    """Compute an HMAC-SHA256 hex signature over the canonical approval decision."""
    key_bytes = get_signing_key(secret_key)
    payload_bytes = canonical_approval_payload(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
    )
    return hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()


def verify_approval_signature(
    *,
    approval_id: str,
    plan_id: str,
    step_ids: list[str],
    decision: str,
    reviewer: str,
    timestamp: str,
    signature: str,
    secret_key: str | None = None,
) -> bool:
    """Verify an approval signature in constant time using hmac.compare_digest."""
    if not signature or not isinstance(signature, str):
        return False
    expected = compute_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
        secret_key=secret_key,
    )
    return hmac.compare_digest(expected, signature)


@dataclass(slots=True)
class SignedApprovalToken:
    """Tamper-evident approval record carrying a cryptographic HMAC signature."""

    approval_id: str
    plan_id: str
    step_ids: list[str]
    decision: str  # "approved" or "rejected"
    reviewer: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    signature: str = ""
    algorithm: str = "HMAC-SHA256"

    def __post_init__(self) -> None:
        if not self.signature:
            self.signature = compute_approval_signature(
                approval_id=self.approval_id,
                plan_id=self.plan_id,
                step_ids=self.step_ids,
                decision=self.decision,
                reviewer=self.reviewer,
                timestamp=self.timestamp,
            )

    def is_valid(self, secret_key: str | None = None) -> bool:
        """Return True if this token has not been tampered with and matches the secret key."""
        return verify_approval_signature(
            approval_id=self.approval_id,
            plan_id=self.plan_id,
            step_ids=self.step_ids,
            decision=self.decision,
            reviewer=self.reviewer,
            timestamp=self.timestamp,
            signature=self.signature,
            secret_key=secret_key,
        )
