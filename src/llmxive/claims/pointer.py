"""T008 — Claim pointer substitution + render (spec 016, PURE / no IO).

Defines its OWN regex for {{claim:<id>}} — agents/prompts.py _TOKEN_RE
matches only [a-z_][a-z0-9_]* and does NOT match the colon in claim:<id>,
so we cannot call prompts.substitute() here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from llmxive.claims.gate import CLAIM_MARKER_PREFIX, strip_claim_artifacts
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus

# Own regex for claim pointers — colon in name requires separate RE.
_CLAIM_POINTER_RE = re.compile(
    r"\{\{\s*claim:(?P<id>c_[0-9a-f]{8})\s*\}\}"
)

# Numeric token AS IT APPEARS in prose (keeps thousands separators + decimal),
# e.g. "27,635", "1,296", "0.95", "1296". A comma/underscore is only consumed
# when it is a genuine thousands separator (followed by exactly 3 digits), so a
# SENTENCE comma after a number ("number 13, the …") is NOT swallowed into the
# token. Matched against raw_text directly so we can swap the as-appears token
# (rendered prose keeps its original grouping where unchanged).
#
# The grouped alternative requires at least one ``[,_]\d{3}`` group (``+`` not
# ``*``); otherwise a bare run of 4+ digits like ``9988`` would be truncated to
# its first three digits (``998``) by the ``\d{1,3}`` prefix, leaving a stray
# ``8`` token — which corrupted rendered prose ("9988" → "99888"). An ungrouped
# integer therefore falls through to the second alternative and is matched whole.
_NUMBER_IN_TEXT_RE = re.compile(r"[-+]?\d{1,3}(?:[,_]\d{3})+(?:\.\d+)?|[-+]?\d+(?:\.\d+)?")


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


def _digits_only(value: str) -> str:
    """Reduce a numeric token to bare digits (drop separators/units/sign)."""
    return "".join(ch for ch in (value or "") if ch.isdigit())


def _numeric_tokens(text: str) -> list[re.Match[str]]:
    """All numeric tokens (as-appears) in ``text``, trailing space/sep trimmed."""
    return list(_NUMBER_IN_TEXT_RE.finditer(text))


# Copula / assignment words that immediately precede the ASSERTED value (the
# "answer") — used to disambiguate it from a qualifier number (a crossing index,
# a year) when the answer carries NO thousands separator. e.g. "… crossing number
# 13 is 27635" → 27635 (not 13); "the total = 9988" → 9988.
_COPULA_RE = re.compile(
    r"(?:\b(?:is|are|was|were|equals?|totals?|yields?|gives?|numbers?|"
    r"amounts?\s+to|comes?\s+to)\b|[=:])\s*$",
    re.IGNORECASE,
)


def _follows_copula(text: str, start: int) -> bool:
    """True iff the numeric token at ``start`` is immediately preceded (allowing
    intervening spaces) by a copula/assignment word — a strong signal that the
    token is the ASSERTED answer rather than a qualifier."""
    return _COPULA_RE.search(text[:start]) is not None


def select_asserted_token(
    text: str, *, resolved_value: str | None = None
) -> re.Match[str] | None:
    """Pick the numeric token in ``text`` that asserts the claimed value.

    SINGLE SOURCE OF TRUTH for "which number does this text assert" — used by
    render (the token swap), ``canonical.subject_key`` (the value-EXCLUDED
    identity), and the fill/smooth layers. A sentence often holds several numbers
    (a parameter/index, a year, AND the asserted count); the deterministic
    disambiguation, in priority order:

    1. A token already equal to ``resolved_value`` (digits-only) — idempotency
       (the prose is already correct; render leaves it untouched).
    2. A token written WITH a thousands separator (``27,635``) — the asserted
       magnitude in scientific prose conventionally carries grouping while
       parameters/years do not. Ordered BEFORE the copula rule so every
       comma-grouped case is byte-identical to the historical behavior (zero
       regression).
    3. A token immediately FOLLOWING a copula/assignment (``is`` / ``=`` / ``:``
       …) — the asserted answer. The fix for non-grouped answers like
       "… crossing number 13 is 27635" (→ 27635, not the qualifier 13).
    4. The FIRST numeric token (historical fallback).

    Returns the positioned :class:`re.Match`, or ``None`` when ``text`` has no
    numeric token.
    """
    matches = list(_NUMBER_IN_TEXT_RE.finditer(text))
    if not matches:
        return None
    if resolved_value:
        rv = _digits_only(resolved_value)
        if rv:
            for m in matches:
                if _digits_only(m.group(0)) == rv:
                    return m
    for m in matches:
        if "," in m.group(0):
            return m
    copula_followed = [m for m in matches if _follows_copula(text, m.start())]
    if copula_followed:
        return copula_followed[-1]  # the last (closest to the final assertion)
    return matches[0]


def asserted_value(text: str, *, resolved_value: str | None = None) -> str | None:
    """The numeric token ``text`` asserts (trimmed string), or ``None``.

    Thin wrapper over :func:`select_asserted_token` — the value-string form used
    by ``canonical.subject_key`` and the fill + smooth layers (which need the
    value, not the position)."""
    m = select_asserted_token(text, resolved_value=resolved_value)
    return m.group(0).strip() if m is not None else None


def _render_numeric(raw_text: str, resolved_value: str) -> str:
    """Swap the asserted numeric token in ``raw_text`` for ``resolved_value``.

    Selects the asserted token (see :func:`select_asserted_token`). If it
    already equals ``resolved_value`` (compared digits-only so ``27,635`` vs
    ``27635`` is an equality), the prose is returned UNCHANGED (idempotency).
    Otherwise that single occurrence is replaced with ``resolved_value`` and all
    surrounding prose is preserved byte-for-byte.
    """
    m = select_asserted_token(raw_text, resolved_value=resolved_value)
    if m is None:
        return raw_text
    matched = m.group(0)
    trimmed = matched.rstrip()  # the [ ] class can capture a trailing space
    start = m.start()
    end = start + len(trimmed)
    # Already-correct (separators stripped) → leave prose intact (idempotent).
    if _digits_only(trimmed) == _digits_only(resolved_value):
        # Distinguish decimals: "28.4" must not be treated equal to "284".
        if "." not in trimmed and "." not in resolved_value:
            return raw_text
        if trimmed == resolved_value:
            return raw_text
    return raw_text[:start] + resolved_value + raw_text[end:]


def _render_entity(raw_text: str, resolved_value: str, kind: ClaimKind) -> str:
    """Swap the asserted object for ``resolved_value`` in an entity/relational claim.

    If ``resolved_value`` already appears in ``raw_text`` → unchanged. Otherwise
    try to identify the asserted object span via ``triple.decompose_triple`` and
    replace it. When the object cannot be confidently located, return ``raw_text``
    UNCHANGED — we never garble prose; citation repair supplies the source.
    """
    if resolved_value and resolved_value in raw_text:
        return raw_text
    from llmxive.claims.triple import decompose_triple

    _subj, _rel, obj = decompose_triple(raw_text)
    obj = (obj or "").strip().rstrip(".")
    if obj and obj in raw_text and obj != resolved_value:
        return raw_text.replace(obj, resolved_value, 1)
    return raw_text


def _render_verified(claim: Claim) -> str:
    """Prose-preserving render of a VERIFIED claim (asserted token → resolved)."""
    raw_text = claim.raw_text
    resolved = claim.resolved_value or ""
    if not resolved:
        return raw_text
    if claim.kind in (ClaimKind.NUMERIC, ClaimKind.RESULT):
        return _render_numeric(raw_text, resolved)
    if claim.kind in (
        ClaimKind.ENTITY_FACT,
        ClaimKind.RELATIONAL,
        ClaimKind.MAGNITUDE,
    ):
        return _render_entity(raw_text, resolved, claim.kind)
    # CITATION / CAUSAL and any other kind: prefer leaving prose intact.
    if resolved in raw_text:
        return raw_text
    # Numeric swap is still the safest mutation when a number is asserted.
    return _render_numeric(raw_text, resolved)


def pointer_ids(text: str) -> list[str]:
    """All claim ids referenced by ``{{claim:<id>}}`` pointers in ``text`` (in order)."""
    return [m.group("id") for m in _CLAIM_POINTER_RE.finditer(text)]


def render(
    text: str,
    claims_by_id: dict[str, Claim],
    *,
    placeholder_verified: bool = False,
) -> tuple[str, GateReport]:
    """Substitute each ``{{claim:<id>}}`` pointer with PROSE, not a bare token.

    Each pointer stands in place of the claim's full ``raw_text`` sentence (the
    span ``process_document`` swapped for the pointer). Rendering therefore
    reconstructs that prose:

    - VERIFIED + ``resolved_value`` present → the claim's ``raw_text`` with ONLY
      the asserted token swapped for ``resolved_value`` (idempotent: an
      already-correct assertion is returned byte-for-byte unchanged).
    - Any other status, or claim_id not in registry → the claim's ``raw_text``
      followed by ONE inline ``[UNRESOLVED-CLAIM: ...]`` marker (the prose is
      preserved; the marker is appended, not substituted for the sentence).

    spec 020 FR-007: when ``placeholder_verified=True`` (the canonical *stored*
    form), a VERIFIED claim keeps its DURABLE ``{{claim:<id>}}`` placeholder rather
    than baking the value into prose — so the value is never re-extractable
    round-to-round (SC-007). The value is substituted only in the rendered VIEW
    (:func:`render_view`) for reviewers + publish (FR-008). Non-verified claims are
    rendered to prose + marker either way.

    Returns ``(rendered_text, GateReport)``.  Pure — no IO.
    """
    report = GateReport()

    def _replace(m: re.Match[str]) -> str:
        cid = m.group("id")
        claim = claims_by_id.get(cid)
        if (
            claim is not None
            and claim.status == ClaimStatus.VERIFIED
            and claim.resolved_value is not None
        ):
            # Durable placeholder in the canonical stored form (FR-007), else bake.
            return m.group(0) if placeholder_verified else _render_verified(claim)
        # Non-verified or unknown → preserve prose + append ONE inline marker.
        reason = (
            f"status={claim.status.value}" if claim is not None else "unknown claim"
        )
        marker = f"{CLAIM_MARKER_PREFIX} {cid} — {reason}]"
        report.blocked = True
        report.unresolved_markers.append(marker)
        if claim is not None and claim.raw_text:
            return f"{claim.raw_text} {marker}"
        return marker

    result = _CLAIM_POINTER_RE.sub(_replace, text)
    return result, report


def drop_orphan_pointers(text: str, known_ids: set[str]) -> str:
    """Remove ``{{claim:<id>}}`` pointers whose id is NOT in ``known_ids`` (orphans).

    spec 020 FR-007: a durable placeholder is preserved only while it has a backing
    registered claim; an orphan pointer (from a deleted claim or hand-edited text)
    is removed so it never renders as a spurious ``unknown claim`` marker.
    """
    def _sub(m: re.Match[str]) -> str:
        return m.group(0) if m.group("id") in known_ids else ""

    cleaned = _CLAIM_POINTER_RE.sub(_sub, text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +([.,;:)])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)  # no trailing space (idempotent fixed point)
    return cleaned


def render_view(text: str, claims_by_id: dict[str, Claim]) -> str:
    """Substitute each VERIFIED ``{{claim:<id>}}`` placeholder with its value-baked prose.

    spec 020 FR-008: the human/reviewer-facing + published view, rendered
    deterministically from the frozen store at review time and for the final
    artifact. A placeholder whose claim is missing or not VERIFIED is left as-is
    (the canonical stored form only carries placeholders for VERIFIED claims).
    Pure — no IO.
    """
    def _sub(m: re.Match[str]) -> str:
        claim = claims_by_id.get(m.group("id"))
        if (
            claim is not None
            and claim.status == ClaimStatus.VERIFIED
            and claim.resolved_value is not None
        ):
            return _render_verified(claim)
        return m.group(0)

    return _CLAIM_POINTER_RE.sub(_sub, text)


__all__ = [
    "GateReport",
    "asserted_value",
    "drop_orphan_pointers",
    "pointer_ids",
    "render",
    "render_view",
    "select_asserted_token",
    "strip_claim_artifacts",
    "substitute_pointers",
    "to_pointer",
]
