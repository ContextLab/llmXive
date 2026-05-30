"""T008 — Claim pointer substitution + render (spec 016, PURE / no IO).

Defines its OWN regex for {{claim:<id>}} — agents/prompts.py _TOKEN_RE
matches only [a-z_][a-z0-9_]* and does NOT match the colon in claim:<id>,
so we cannot call prompts.substitute() here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from llmxive.claims.gate import CLAIM_MARKER_PREFIX
from llmxive.claims.models import Claim, ClaimStatus

# Own regex for claim pointers — colon in name requires separate RE.
_CLAIM_POINTER_RE = re.compile(
    r"\{\{\s*claim:(?P<id>c_[0-9a-f]{8})\s*\}\}"
)


@dataclass
class GateReport:
    """Summary of one render pass — whether any unresolved claim blocks output."""

    blocked: bool = False
    unresolved_markers: list[str] = field(default_factory=list)


def to_pointer(claim_id: str) -> str:
    """Format a claim id as an in-document pointer ``{{claim:<id>}}``."""
    return f"{{{{claim:{claim_id}}}}}"


def substitute_pointers(text: str, spans: list[tuple[str, str]]) -> str:
    """Replace each raw ``span`` string with its ``{{claim:<id>}}`` pointer.

    Idempotent: spans that are already rendered as pointers are not
    double-wrapped (the pointer string does not contain the raw span).
    """
    for raw_span, claim_id in spans:
        pointer = to_pointer(claim_id)
        # Only replace occurrences that are NOT already inside a pointer.
        # Simple approach: replace raw_span when it does not appear immediately
        # after "{{claim:" — this handles the common idempotency case.
        if raw_span in text and pointer not in text:
            text = text.replace(raw_span, pointer)
    return text


def render(text: str, claims_by_id: dict[str, Claim]) -> tuple[str, GateReport]:
    """Substitute each ``{{claim:<id>}}`` pointer with its resolved value or marker.

    - VERIFIED claim  → ``resolved_value`` (the only trusted value)
    - Any other status, or claim_id not in registry → ``[UNRESOLVED-CLAIM: ...]``

    Returns ``(rendered_text, GateReport)``.  Pure — no IO.
    """
    report = GateReport()
    result = text

    def _replace(m: re.Match[str]) -> str:
        cid = m.group("id")
        claim = claims_by_id.get(cid)
        if claim is not None and claim.status == ClaimStatus.VERIFIED and claim.resolved_value is not None:
            return claim.resolved_value
        # Non-verified or unknown → unified marker
        reason = f"status={claim.status.value}" if claim is not None else "unknown claim"
        marker = f"{CLAIM_MARKER_PREFIX} {cid} — {reason}]"
        report.blocked = True
        report.unresolved_markers.append(marker)
        return marker

    result = _CLAIM_POINTER_RE.sub(_replace, result)
    return result, report


__all__ = ["GateReport", "render", "substitute_pointers", "to_pointer"]
