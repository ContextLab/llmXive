"""T004 — Claim entity model (spec 016, data-model.md)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum


class ClaimKind(str, Enum):  # noqa: UP042 - str+Enum mixin kept; StrEnum changes str() repr
    NUMERIC = "numeric"
    MAGNITUDE = "magnitude"
    RELATIONAL = "relational"
    CAUSAL = "causal"
    ENTITY_FACT = "entity_fact"
    CITATION = "citation"
    RESULT = "result"


class ClaimStatus(str, Enum):  # noqa: UP042 - str+Enum mixin kept; StrEnum changes str() repr
    PENDING = "pending"
    VERIFIED = "verified"
    REFUTED = "refuted"
    NOT_ENOUGH_INFO = "not_enough_info"
    UNRESOLVABLE = "unresolvable"


@dataclass(frozen=True)
class Verdict:
    """Resolution outcome for one claim (pure data, frozen)."""

    status: ClaimStatus
    value: str | None
    evidence: dict | None
    resolver: str | None


@dataclass
class Claim:
    """One verifiable claim extracted from an artifact (spec 016 data-model)."""

    claim_id: str
    kind: ClaimKind
    raw_text: str
    canonical: str
    context: str
    artifact_path: str
    source_type: str  # "external" | "result" | "pending"
    status: ClaimStatus
    resolved_value: str | None
    evidence: dict | None
    resolver: str | None
    attempts: int
    updated_at: str  # ISO timestamp; stamped by caller
    # US4 (T035): hash of the underlying source or receipt artifact at the time
    # of resolution; a change forces re-resolution (FR-015 invalidation).
    source_hash: str | None = None


def compute_claim_id(kind: ClaimKind, canonical: str, context: str) -> str:
    """Stable, deterministic claim identity: ``c_`` + first 8 hex chars of sha256.

    The hash input is ``kind.value + "\\x00" + canonical + "\\x00" + context``
    so each component is clearly delimited and any single change produces a
    different id.
    """
    payload = f"{kind.value}\x00{canonical}\x00{context}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return "c_" + digest[:8]


__all__ = [
    "Claim",
    "ClaimKind",
    "ClaimStatus",
    "Verdict",
    "compute_claim_id",
]
