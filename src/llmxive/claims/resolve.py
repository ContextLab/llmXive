"""T014 — Claim resolver dispatch (spec 016, US1).

select_resolver(kind) -> Callable
resolve(claim, *, backend, model, repo_root) -> Verdict

NUMERIC / CITATION: real resolution via librarian.verify.resolve_reference
(existence) + grounding.service.ground_cited_claim (content gate).
Absence of evidence → NOT_ENOUGH_INFO; source contradicts → REFUTED.

MAGNITUDE / RELATIONAL / CAUSAL / ENTITY_FACT / RESULT: thin honest
NOT_ENOUGH_INFO stubs; full implementation in US2/US3 (T027/T031/T032).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, Verdict
from llmxive.grounding import cache as _cache

logger = logging.getLogger(__name__)

# Reasoning-safe token budget (mirrors grounding/entailment.py F-13 fix).
_REASONING_MAX_TOKENS = 131_072
_DEFAULT_MODEL = "qwen.qwen3.5-122b"


# ---------------------------------------------------------------------------
# US1 — numeric / citation resolver (full implementation)
# ---------------------------------------------------------------------------

def resolve_numeric_or_citation(claim: Claim, *, backend: Any, model: str | None,
                                 repo_root: Path) -> Verdict:
    """Resolve a NUMERIC or CITATION claim via existence check + content gate.

    Outcome policy:
    - Source does not exist (unreachable)        → NOT_ENOUGH_INFO
    - Source exists but content absent/fails     → NOT_ENOUGH_INFO
    - Source content contradicts                 → REFUTED
    - Source content supports (number present)   → VERIFIED
    Absence of evidence NEVER maps to VERIFIED.
    """
    from llmxive.agents.grounding_guard import CitedClaim, classify_source
    from llmxive.grounding.service import ground_cited_claim, number_substantiated
    from llmxive.librarian.verify import resolve_reference
    from llmxive.types import CitationKind

    canonical = claim.canonical or claim.raw_text
    kind_str, source_value = classify_source(canonical)

    # If no resolvable identifier in the canonical text, try raw_text.
    if kind_str is None:
        kind_str, source_value = classify_source(claim.raw_text or "")

    # No resolvable source → cannot verify, not refuted, just insufficient info.
    if kind_str is None or source_value is None:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no resolvable source identifier (DOI/arXiv/URL) found in claim"},
            resolver="resolve_numeric_or_citation",
        )

    source_id = f"{kind_str.value}:{source_value}"

    # Check the verdict cache first.
    cached = _cache.get_verdict(
        repo_root,
        source_id=source_id,
        claim=canonical,
        number=_extract_number(canonical),
    )
    if cached is not None:
        status = _map_cached_status(cached)
        return Verdict(
            status=status,
            value=cached.get("value"),
            evidence=cached,
            resolver="resolve_numeric_or_citation",
        )

    # Step 1: existence check (anti-fabrication gate).
    outcome = resolve_reference(kind_str.value, source_value)
    if not outcome.present:
        # Source does not exist → not enough info (absence of evidence ≠ refuted).
        result = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": f"source unreachable: {outcome.reason}", "url": outcome.resolved_url},
            resolver="resolve_numeric_or_citation",
        )
        _cache.put_verdict(
            repo_root,
            source_id=source_id,
            claim=canonical,
            number=_extract_number(canonical),
            verdict={"status": "not_enough_info", "ok": False,
                     "reason": result.evidence["reason"] if result.evidence else ""},
        )
        return result

    # Step 2: content gate via grounding service.
    number = _extract_number(canonical)
    cited = CitedClaim(
        claim_text=canonical,
        number=number,
        source_str=canonical,
        source_kind=kind_str,
        source_value=source_value,
    )
    grounding = ground_cited_claim(cited, backend=backend, model=model or _DEFAULT_MODEL,
                                   repo_root=repo_root)

    if grounding.ok:
        status = ClaimStatus.VERIFIED
    else:
        # Distinguish: was the source content contradictory or just missing?
        reason_lower = (grounding.reason or "").lower()
        if "contradict" in reason_lower or "wrong" in reason_lower or "incorrect" in reason_lower:
            status = ClaimStatus.REFUTED
        else:
            # Source retrieved but claim not found / number mismatch → not enough info.
            # This is DISTINCT from REFUTED (source contradicts).
            status = ClaimStatus.NOT_ENOUGH_INFO

    return Verdict(
        status=status,
        value=None,
        evidence={"ok": grounding.ok, "reason": grounding.reason},
        resolver="resolve_numeric_or_citation",
    )


def _extract_number(text: str) -> str | None:
    """Extract the first salient numeric token from text (for the number gate)."""
    import re
    m = re.search(r"[-+]?\d[\d,_ ]*(?:\.\d+)?", text or "")
    if not m:
        return None
    from llmxive.agents.grounding_guard import _clean_number_token
    return _clean_number_token(m.group(0))


def _map_cached_status(cached: dict) -> ClaimStatus:
    raw = cached.get("status", "")
    mapping = {
        "verified": ClaimStatus.VERIFIED,
        "refuted": ClaimStatus.REFUTED,
        "not_enough_info": ClaimStatus.NOT_ENOUGH_INFO,
        "not_found": ClaimStatus.NOT_ENOUGH_INFO,
        "unresolvable": ClaimStatus.NOT_ENOUGH_INFO,
    }
    return mapping.get(raw, ClaimStatus.NOT_ENOUGH_INFO)


# ---------------------------------------------------------------------------
# US2/US3 stubs — honest NOT_ENOUGH_INFO (full impl in later tasks)
# ---------------------------------------------------------------------------

def resolve_magnitude(claim: Claim, *, backend: Any, model: str | None,
                      repo_root: Path) -> Verdict:
    """MAGNITUDE resolver — full implementation deferred to US3 (T031/T032)."""
    return Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={"note": "resolver not yet wired (US2/US3)"},
        resolver="resolve_magnitude",
    )


def resolve_relational(claim: Claim, *, backend: Any, model: str | None,
                       repo_root: Path) -> Verdict:
    """RELATIONAL resolver — full implementation deferred to US3 (T031/T032)."""
    return Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={"note": "resolver not yet wired (US2/US3)"},
        resolver="resolve_relational",
    )


def resolve_causal(claim: Claim, *, backend: Any, model: str | None,
                   repo_root: Path) -> Verdict:
    """CAUSAL resolver — full implementation deferred to US3 (T032)."""
    return Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={"note": "resolver not yet wired (US2/US3)"},
        resolver="resolve_causal",
    )


def resolve_entity_fact(claim: Claim, *, backend: Any, model: str | None,
                        repo_root: Path) -> Verdict:
    """ENTITY_FACT resolver — full implementation deferred to US3 (T032)."""
    return Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={"note": "resolver not yet wired (US2/US3)"},
        resolver="resolve_entity_fact",
    )


def resolve_result(claim: Claim, *, backend: Any, model: str | None,
                   repo_root: Path) -> Verdict:
    """RESULT resolver — full implementation deferred to US2 (T027)."""
    return Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={"note": "resolver not yet wired (US2/US3)"},
        resolver="resolve_result",
    )


# ---------------------------------------------------------------------------
# Dispatch table + public API
# ---------------------------------------------------------------------------

_DISPATCH: dict[ClaimKind, Callable] = {
    ClaimKind.NUMERIC: resolve_numeric_or_citation,
    ClaimKind.CITATION: resolve_numeric_or_citation,
    ClaimKind.MAGNITUDE: resolve_magnitude,
    ClaimKind.RELATIONAL: resolve_relational,
    ClaimKind.CAUSAL: resolve_causal,
    ClaimKind.ENTITY_FACT: resolve_entity_fact,
    ClaimKind.RESULT: resolve_result,
}


def select_resolver(kind: ClaimKind) -> Callable:
    """Return the resolver callable for the given ClaimKind."""
    return _DISPATCH[kind]


def resolve(claim: Claim, *, backend: Any, model: str | None,
            repo_root: Path) -> Verdict:
    """Dispatch to the correct resolver for ``claim.kind``.

    Returns a :class:`Verdict` — never raises. On any unexpected error
    returns NOT_ENOUGH_INFO (fail-safe: absence of evidence ≠ verified).
    """
    resolver_fn = select_resolver(claim.kind)
    try:
        return resolver_fn(claim, backend=backend, model=model, repo_root=repo_root)
    except Exception as exc:
        logger.warning("claims.resolve: resolver %s failed for %s (%s: %s)",
                       resolver_fn.__name__, claim.claim_id, type(exc).__name__, exc)
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"error": f"{type(exc).__name__}: {exc}"},
            resolver=resolver_fn.__name__,
        )


__all__ = ["resolve", "select_resolver"]
