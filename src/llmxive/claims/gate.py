"""T010 — Unified claim marker + block predicates (spec 016).

API mirrors agents/citation_guard.py F-18 predicates so convergence/engine.py
detects claim blocks the same way it detected [UNVERIFIED].
"""

from __future__ import annotations

import re

from llmxive.claims.models import Claim

# Single source of truth for the unified claim-marker prefix (FR-019).
CLAIM_MARKER_PREFIX = "[UNRESOLVED-CLAIM:"

# Locates a whole marker, capturing its body for reporting.
_UNRESOLVED_MARKER_RE = re.compile(
    re.escape(CLAIM_MARKER_PREFIX) + r"\s*(?P<body>[^\]]*?)\s*\]"
)


def mark_unresolved(text: str, claim: Claim, reason: str) -> str:
    """Append an [UNRESOLVED-CLAIM: <id> — <reason>] marker to ``text``."""
    marker = f"{CLAIM_MARKER_PREFIX} {claim.claim_id} — {reason}]"
    return f"{text} {marker}"


def has_unresolved_claims(text: str) -> bool:
    """True iff ``text`` contains at least one [UNRESOLVED-CLAIM: ...] marker."""
    return CLAIM_MARKER_PREFIX in text


def find_unresolved_claims(text: str) -> list[str]:
    """Return the body of every [UNRESOLVED-CLAIM: ...] marker in document order."""
    return [m.group("body").strip() for m in _UNRESOLVED_MARKER_RE.finditer(text)]


__all__ = [
    "CLAIM_MARKER_PREFIX",
    "find_unresolved_claims",
    "has_unresolved_claims",
    "mark_unresolved",
]
