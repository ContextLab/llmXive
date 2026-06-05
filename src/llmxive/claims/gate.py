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

# Stray claim-layer pointer ``{{claim:<id>}}`` (mirrors pointer._CLAIM_POINTER_RE;
# duplicated here to avoid an import cycle — gate.py is imported BY pointer.py).
_STRAY_POINTER_RE = re.compile(r"\{\{\s*claim:c_[0-9a-f]{8}\s*\}\}")


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


def strip_claim_artifacts(text: str, *, preserve_pointers: bool = False) -> str:
    """Remove prior claim-layer artifacts so a re-run does not re-extract them.

    The claim layer runs once per reviser round. Without this, the markers and
    pointers it injected last round become INPUT this round: the extractor lifts
    an ``[UNRESOLVED-CLAIM: <id> — <reason>]`` body as a brand-new "claim" (whose
    text is literally a marker reason) and a stray ``{{claim:<id>}}`` pointer
    survives into the rendered prose. Stripping both at the top of
    ``process_document`` makes the pass idempotent.

    Removes every whole ``[UNRESOLVED-CLAIM: … ]`` span (to its closing ``]``)
    and every stray ``{{claim:<id>}}`` pointer, then collapses the doubled spaces
    a removal can leave WITHIN a line (newlines preserved). PURE — no IO.

    spec 020 FR-007: with ``preserve_pointers=True`` the durable ``{{claim:<id>}}``
    placeholders that carry a verified value in the canonical stored form are KEPT
    (only the transient ``[UNRESOLVED-CLAIM: … ]`` markers are removed), so the
    value is never re-extractable round-to-round (SC-007). The default keeps the
    legacy behavior (also strip pointers) for every existing caller.
    """
    cleaned = _UNRESOLVED_MARKER_RE.sub("", text)
    if not preserve_pointers:
        cleaned = _STRAY_POINTER_RE.sub("", cleaned)
    # Collapse runs of spaces/tabs a removal leaves behind, without touching
    # newlines (so paragraph structure is preserved). Also tidy " ." → ".".
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +([.,;:)])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    return cleaned


__all__ = [
    "CLAIM_MARKER_PREFIX",
    "find_unresolved_claims",
    "has_unresolved_claims",
    "mark_unresolved",
    "strip_claim_artifacts",
]
