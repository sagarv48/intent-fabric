"""Evidence provenance verifier for Knowledge Fabric → Intent Fabric contract.

Re-computes SHA-256 hashes independently and compares them against the
values reported by Knowledge Fabric to detect tampering or corruption.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class VerificationResult:
    """Outcome of evidence provenance verification."""

    is_valid: bool
    checked_chunks: int
    failed_chunks: list[str]  # chunk_ids that failed hash verification
    digest_valid: bool
    fingerprint_present: bool
    freshness_valid: bool
    errors: list[str]


def compute_chunk_hash(document_uri: str, snippet: str) -> str:
    """Re-compute SHA-256 provenance hash for a single evidence chunk.

    Must produce identical output to knowledge_fabric.evidence.models.compute_chunk_hash().
    Formula: SHA-256(document_uri + ":" + snippet)
    """
    payload = f"{document_uri}:{snippet}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_package_digest(provenance_hashes: list[str]) -> str:
    """Re-compute composite SHA-256 digest over ordered chunk hashes.

    Formula: SHA-256(hash_1 + ":" + hash_2 + ":" + ... + hash_N)
    """
    if not provenance_hashes:
        return ""
    combined = ":".join(provenance_hashes).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def verify_evidence(
    payload: dict[str, object],
    *,
    max_age_seconds: float = 60.0,
) -> VerificationResult:
    """Verify cryptographic provenance of an evidence payload from Knowledge Fabric.

    Checks:
      1. Each chunk's provenance_hash matches re-computed SHA-256(document_uri:snippet).
      2. The package provenance_digest matches re-computed SHA-256 over ordered chunk hashes.
      3. query_fingerprint is present and non-empty.
      4. generated_at timestamp is within max_age_seconds of current time.

    Args:
        payload: The dict returned by Knowledge Fabric's retrieve_evidence MCP tool.
        max_age_seconds: Maximum acceptable age of evidence in seconds (default: 60).

    Returns:
        VerificationResult with detailed pass/fail status for each check.
    """
    errors: list[str] = []
    failed_chunks: list[str] = []

    items = payload.get("items", [])
    if not isinstance(items, list):
        return VerificationResult(
            is_valid=False,
            checked_chunks=0,
            failed_chunks=[],
            digest_valid=False,
            fingerprint_present=False,
            freshness_valid=False,
            errors=["'items' field is missing or not a list"],
        )

    # 1. Verify individual chunk provenance hashes
    recomputed_hashes: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        document_uri = str(item.get("document_uri", ""))
        snippet = str(item.get("snippet", ""))
        reported_hash = str(item.get("provenance_hash", ""))
        chunk_id = item.get("chunk_id", "unknown")

        expected_hash = compute_chunk_hash(document_uri, snippet)
        recomputed_hashes.append(expected_hash)

        if reported_hash and reported_hash != expected_hash:
            failed_chunks.append(str(chunk_id))
            errors.append(
                f"Chunk {chunk_id}: provenance_hash mismatch "
                f"(reported={reported_hash[:16]}..., expected={expected_hash[:16]}...)"
            )

    # 2. Verify package digest
    reported_digest = str(payload.get("provenance_digest", ""))
    expected_digest = compute_package_digest(recomputed_hashes)
    digest_valid = (
        reported_digest == expected_digest if reported_digest else len(items) == 0
    )
    if not digest_valid:
        errors.append(
            f"Package digest mismatch "
            f"(reported={reported_digest[:16]}..., expected={expected_digest[:16]}...)"
        )

    # 3. Check query fingerprint presence
    fingerprint = str(payload.get("query_fingerprint", ""))
    fingerprint_present = bool(fingerprint and len(fingerprint) == 64)
    if not fingerprint_present:
        errors.append("query_fingerprint is missing or malformed (expected 64-char hex)")

    # 4. Check freshness
    freshness_valid = True
    generated_at_str = str(payload.get("generated_at", ""))
    if generated_at_str:
        try:
            generated_at = datetime.fromisoformat(generated_at_str)
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=UTC)
            age = (datetime.now(UTC) - generated_at).total_seconds()
            if age > max_age_seconds:
                freshness_valid = False
                errors.append(f"Evidence is {age:.1f}s old (max: {max_age_seconds}s)")
        except (ValueError, TypeError):
            freshness_valid = False
            errors.append(f"Cannot parse generated_at: {generated_at_str!r}")

    is_valid = (
        len(failed_chunks) == 0
        and digest_valid
        and fingerprint_present
        and freshness_valid
    )

    return VerificationResult(
        is_valid=is_valid,
        checked_chunks=len(items),
        failed_chunks=failed_chunks,
        digest_valid=digest_valid,
        fingerprint_present=fingerprint_present,
        freshness_valid=freshness_valid,
        errors=errors,
    )
