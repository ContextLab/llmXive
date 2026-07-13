"""T004 — Claim entity model (spec 016, data-model.md)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    evidence: dict[str, Any] | None
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
    evidence: dict[str, Any] | None
    resolver: str | None
    attempts: int
    updated_at: str  # ISO timestamp; stamped by caller
    # US4 (T035): hash of the underlying source or receipt artifact at the time
    # of resolution; a change forces re-resolution (FR-015 invalidation).
    source_hash: str | None = None


#: Markers the claims layer itself STAMPS BACK INTO the artifact it extracted from:
#: the ``[UNRESOLVED-CLAIM: <id> — …]`` / ``[UNVERIFIED: …]`` quality markers and the
#: ``{{claim:<id>}}`` pointers. They are the layer's own bookkeeping, NOT part of what
#: a claim asserts — so they must not participate in the claim's identity.
_SELF_STAMPED_RE = re.compile(
    r"\[(?:UNRESOLVED-CLAIM|UNVERIFIED):[^\]]*\]|\{\{claim:[^}]*\}\}"
)


def _identity_text(text: str) -> str:
    """Normalize a hash input so re-extraction is IDEMPOTENT.

    ``context`` is the LLM's free-text quote of the surrounding artifact text — and
    the claims layer injects its markers back INTO that artifact. So on the next tick
    the quoted context contained the marker minted on the PREVIOUS tick, hashing to a
    NEW id for the SAME claim: a self-referential feedback loop. It churned the
    registry to 20,272 entries for 13,894 distinct canonical claims (one claim seen
    under 59 ids), meant the resolution cache NEVER hit (every claim re-resolved from
    scratch, every tick), and rewrote the artifact's prose each pass — which is what
    destabilized task identity in tasks.md. Strip the layer's own stamps and collapse
    whitespace so identity depends only on what the claim actually SAYS."""
    return " ".join(_SELF_STAMPED_RE.sub(" ", text).split())


def compute_claim_id(kind: ClaimKind, canonical: str, context: str) -> str:
    """Stable, deterministic claim identity: ``c_`` + first 8 hex chars of sha256.

    The hash input is ``kind.value + "\\x00" + canonical + "\\x00" + context`` so each
    component is clearly delimited and any single change produces a different id.
    Both text components are normalized by :func:`_identity_text` first, so a claim
    keeps ONE id across re-extraction of an artifact the layer has annotated.
    """
    payload = f"{kind.value}\x00{_identity_text(canonical)}\x00{_identity_text(context)}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return "c_" + digest[:8]


__all__ = [
    "Claim",
    "ClaimKind",
    "ClaimStatus",
    "Verdict",
    "compute_claim_id",
]
