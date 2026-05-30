"""T014/T032 — Claim resolver dispatch (spec 016, US1/US3).

select_resolver(kind) -> Callable
resolve(claim, *, backend, model, repo_root) -> Verdict

NUMERIC / CITATION: real resolution via librarian.verify.resolve_reference
(existence) + grounding.service.ground_cited_claim (content gate).
Absence of evidence → NOT_ENOUGH_INFO; source contradicts → REFUTED.

MAGNITUDE / RELATIONAL: real resolution via claims.triple (T031/T032).
CAUSAL: requires a citable supporting source (retrieve+assess); never infers
  VERIFIED from model text alone; else NOT_ENOUGH_INFO.
ENTITY_FACT: authoritative-reference entailment (retrieve+assess).
RESULT: signed receipt verification (T027/US2).

T019 (spec 017): when LLMXIVE_CLAIM_FILL=1 and the resolver would return
NOT_ENOUGH_INFO or REFUTED, fill_claim() is called first; a filled result
upgrades the outcome to VERIFIED.  RESULT claims are never filled.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, Verdict
from llmxive.grounding import cache as _cache

if TYPE_CHECKING:
    from llmxive.verify.constants import CuratedConstant

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
    from llmxive.grounding.service import ground_cited_claim
    from llmxive.librarian.verify import resolve_reference

    canonical = claim.canonical or claim.raw_text
    kind_str, source_value = classify_source(canonical)

    # If no resolvable identifier in the canonical text, try raw_text.
    if kind_str is None:
        kind_str, source_value = classify_source(claim.raw_text or "")

    # No resolvable source → cannot verify, not refuted, just insufficient info.
    if kind_str is None or source_value is None:
        nei = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no resolvable source identifier (DOI/arXiv/URL) found in claim"},
            resolver="resolve_numeric_or_citation",
        )
        return _maybe_fill(claim, nei, backend=backend, model=model, repo_root=repo_root)

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
        _nei = Verdict(
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
                     "reason": _nei.evidence["reason"] if _nei.evidence else ""},
        )
        return _maybe_fill(claim, _nei, backend=backend, model=model, repo_root=repo_root)

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

    final = Verdict(
        status=status,
        value=None,
        evidence={"ok": grounding.ok, "reason": grounding.reason},
        resolver="resolve_numeric_or_citation",
    )
    if status in (ClaimStatus.NOT_ENOUGH_INFO, ClaimStatus.REFUTED):
        return _maybe_fill(claim, final, backend=backend, model=model, repo_root=repo_root)
    return final


def _maybe_fill(
    claim: Claim,
    original_verdict: Verdict,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path,
) -> Verdict:
    """Attempt authoritative fill when LLMXIVE_CLAIM_FILL=1.

    If fill succeeds, returns a VERIFIED Verdict with fill provenance.
    Otherwise returns *original_verdict* unchanged.

    Never called for RESULT claims (spec 017 T019 constraint).
    """
    if os.environ.get("LLMXIVE_CLAIM_FILL") != "1":
        return original_verdict
    if claim.kind == ClaimKind.RESULT:
        return original_verdict

    try:
        from llmxive.fill.service import fill_claim
        fill_result = fill_claim(claim, backend=backend, model=model, repo_root=repo_root)
    except Exception as exc:
        logger.warning("claims.resolve._maybe_fill: fill_claim raised %s: %s",
                       type(exc).__name__, exc)
        return original_verdict

    if fill_result.status != "filled":
        return original_verdict

    prov = fill_result.provenance
    assert prov is not None
    return Verdict(
        status=ClaimStatus.VERIFIED,
        value=fill_result.value,
        evidence={
            "filled": True,
            "fill": prov.to_dict(),
        },
        resolver=f"fill:{prov.channel}",
    )


def _extract_number(text: str) -> str | None:
    """Extract the first salient numeric token from text (for the number gate)."""
    import re
    m = re.search(r"[-+]?\d[\d,_ ]*(?:\.\d+)?", text or "")
    if not m:
        return None
    from llmxive.agents.grounding_guard import _clean_number_token
    return _clean_number_token(m.group(0))


def _map_cached_status(cached: dict[str, Any]) -> ClaimStatus:
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
# US3 — non-numeric resolvers (T031/T032)
# ---------------------------------------------------------------------------

def resolve_magnitude(claim: Claim, *, backend: Any, model: str | None,
                      repo_root: Path) -> Verdict:
    """MAGNITUDE (superlative/comparative) resolver — retrieve candidate set → ordering.

    Delegates to ``claims.triple.resolve_superlative``.  Returns VERIFIED if
    the claimed extremum is supported by a retrieved candidate set, REFUTED if
    the ordering contradicts it, NOT_ENOUGH_INFO if no source can be retrieved.

    When LLMXIVE_CLAIM_FILL=1, a NEI or REFUTED result is passed to
    ``_maybe_fill`` so a wrong superlative may be corrected from a fetched
    candidate set (spec 018, T020/US3).
    """
    from llmxive.claims.triple import resolve_superlative
    verdict = resolve_superlative(claim, backend=backend, model=model, repo_root=repo_root)
    if verdict.status in (ClaimStatus.NOT_ENOUGH_INFO, ClaimStatus.REFUTED):
        return _maybe_fill(claim, verdict, backend=backend, model=model, repo_root=repo_root)
    return verdict


def resolve_relational(claim: Claim, *, backend: Any, model: str | None,
                       repo_root: Path) -> Verdict:
    """RELATIONAL (SPO) resolver — decompose → retrieve citable source → entailment.

    Delegates to ``claims.triple.resolve_relational``.  Returns VERIFIED only
    when a citable source supports the claim; REFUTED if contradicted; else
    NOT_ENOUGH_INFO.  Never infers VERIFIED from model text alone.

    When LLMXIVE_CLAIM_FILL=1, a NEI or REFUTED result is passed to
    ``_maybe_fill`` so the correct object may be filled from a fetched source
    (spec 018, T023/US4).  FR-009: if the fill service returns the claimed
    object (because it is one of several valid objects), VERIFIED is returned
    without over-correcting.
    """
    from llmxive.claims.triple import resolve_relational as _triple_resolve_relational
    verdict = _triple_resolve_relational(claim, backend=backend, model=model,
                                         repo_root=repo_root)
    if verdict.status in (ClaimStatus.NOT_ENOUGH_INFO, ClaimStatus.REFUTED):
        return _maybe_fill(claim, verdict, backend=backend, model=model, repo_root=repo_root)
    return verdict


def resolve_causal(claim: Claim, *, backend: Any, model: str | None,
                   repo_root: Path) -> Verdict:
    """CAUSAL resolver — requires a citable supporting source; else NOT_ENOUGH_INFO.

    Steps:
    1. Retrieve a source via librarian (Semantic Scholar / full_text cascade).
    2. Run entailment: grounded → VERIFIED, contradicted → REFUTED.
    3. If no source is found OR entailment returns not_found → NOT_ENOUGH_INFO.
    NEVER returns VERIFIED from model inference alone.
    """
    from llmxive.claims.triple import _search_for_source
    from llmxive.grounding.entailment import assess

    canonical = (claim.canonical or claim.raw_text or "").strip()
    if not canonical:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "empty canonical text"},
            resolver="resolve_causal",
        )

    doc = _search_for_source(canonical, backend=backend, model=model,
                              repo_root=repo_root)

    if doc is None or not doc.readable:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no citable source found for causal claim"},
            resolver="resolve_causal",
        )

    verdict = assess(canonical, doc, backend=backend, model=model,
                     repo_root=repo_root)

    if verdict.status == "grounded":
        return Verdict(
            status=ClaimStatus.VERIFIED,
            value=canonical,
            evidence={
                "source_url": doc.final_url,
                "entailment_status": verdict.status,
                "entailment_evidence": verdict.evidence,
            },
            resolver="resolve_causal",
        )
    if verdict.status == "contradicted":
        return Verdict(
            status=ClaimStatus.REFUTED,
            value=None,
            evidence={
                "source_url": doc.final_url,
                "entailment_status": verdict.status,
                "entailment_evidence": verdict.evidence,
            },
            resolver="resolve_causal",
        )

    # not_found: source retrieved but doesn't address the causal claim
    return Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={
            "reason": "source found but does not address causal claim",
            "source_url": doc.final_url,
            "entailment_status": verdict.status,
        },
        resolver="resolve_causal",
    )


def resolve_entity_fact(claim: Claim, *, backend: Any, model: str | None,
                        repo_root: Path) -> Verdict:
    """ENTITY_FACT resolver — authoritative reference entailment.

    Steps:
    1. Retrieve a definitional/authoritative source (Wikipedia, S2, arXiv).
    2. Run entailment: grounded → VERIFIED, contradicted → REFUTED,
       not_found → NOT_ENOUGH_INFO.
    NEVER returns VERIFIED from model inference alone.
    """
    from llmxive.claims.triple import _search_for_source
    from llmxive.grounding.entailment import assess

    canonical = (claim.canonical or claim.raw_text or "").strip()
    if not canonical:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "empty canonical text"},
            resolver="resolve_entity_fact",
        )

    doc = _search_for_source(canonical, backend=backend, model=model,
                              repo_root=repo_root)

    if doc is None or not doc.readable:
        _nei_no_src = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no authoritative source found for entity claim"},
            resolver="resolve_entity_fact",
        )
        return _maybe_fill(claim, _nei_no_src, backend=backend, model=model, repo_root=repo_root)

    verdict = assess(canonical, doc, backend=backend, model=model,
                     repo_root=repo_root)

    if verdict.status == "grounded":
        return Verdict(
            status=ClaimStatus.VERIFIED,
            value=canonical,
            evidence={
                "source_url": doc.final_url,
                "entailment_status": verdict.status,
                "entailment_evidence": verdict.evidence,
            },
            resolver="resolve_entity_fact",
        )
    if verdict.status == "contradicted":
        _refuted = Verdict(
            status=ClaimStatus.REFUTED,
            value=None,
            evidence={
                "source_url": doc.final_url,
                "entailment_status": verdict.status,
                "entailment_evidence": verdict.evidence,
            },
            resolver="resolve_entity_fact",
        )
        return _maybe_fill(claim, _refuted, backend=backend, model=model, repo_root=repo_root)

    _nei = Verdict(
        status=ClaimStatus.NOT_ENOUGH_INFO,
        value=None,
        evidence={
            "reason": "source found but does not address entity claim",
            "source_url": doc.final_url,
            "entailment_status": verdict.status,
        },
        resolver="resolve_entity_fact",
    )
    return _maybe_fill(claim, _nei, backend=backend, model=model, repo_root=repo_root)


def _extract_project_id(artifact_path: str) -> str | None:
    """Extract the project identifier from a repo-relative artifact path.

    Handles paths like:
        ``projects/PROJ-552-some-name/specs/foo.md``  → ``PROJ-552-some-name``
        ``PROJ-001/bar.md``                           → ``PROJ-001``
        ``PROJ-001``                                  → ``PROJ-001``

    Returns None when no PROJ-NNN pattern is found.
    """
    import re
    m = re.search(r"(PROJ-[A-Za-z0-9_-]+)", artifact_path or "")
    return m.group(1) if m else None


def resolve_result(claim: Claim, *, backend: Any, model: str | None,
                   repo_root: Path) -> Verdict:
    """RESULT resolver (T027 — US2).

    Resolution policy:
    - A signed receipt exists whose output_sha256 matches the claim's
      canonical value AND verify_receipt passes  → VERIFIED.
      The verdict carries ``result_id`` in ``evidence`` so a downstream
      citation pointer ``result:<result_id>`` (FR-010) can be formed.
    - No matching receipt, or HMAC verification fails (SC-004)  →
      NOT_ENOUGH_INFO (block; absence of receipt ≠ REFUTED).
    """
    from llmxive.results.harness import result_backed

    # The canonical field holds the value the model wrote; extract it.
    candidate_value = claim.canonical or claim.raw_text

    # Derive project_id from the artifact_path (repo-relative, e.g.
    # "projects/PROJ-552-knots/implementation_plan.md").
    project_id = _extract_project_id(claim.artifact_path or "")

    receipt = None
    if project_id:
        receipt = result_backed(candidate_value, project_id,
                                repo_root=repo_root)

    if receipt is None:
        return Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={
                "note": "no signed receipt backing this result value (SC-004)",
                "candidate_value": candidate_value,
                "project_id": project_id,
            },
            resolver="resolve_result",
        )

    return Verdict(
        status=ClaimStatus.VERIFIED,
        value=receipt.value,
        evidence={
            "result_id": receipt.result_id,
            "output_sha256": receipt.output_sha256,
            "created_at": receipt.created_at,
            "source": f"result:{receipt.result_id}",
        },
        resolver="resolve_result",
    )


# ---------------------------------------------------------------------------
# Dispatch table + public API
# ---------------------------------------------------------------------------

_DISPATCH: dict[ClaimKind, Callable[..., Verdict]] = {
    ClaimKind.NUMERIC: resolve_numeric_or_citation,
    ClaimKind.CITATION: resolve_numeric_or_citation,
    ClaimKind.MAGNITUDE: resolve_magnitude,
    ClaimKind.RELATIONAL: resolve_relational,
    ClaimKind.CAUSAL: resolve_causal,
    ClaimKind.ENTITY_FACT: resolve_entity_fact,
    ClaimKind.RESULT: resolve_result,
}


def select_resolver(kind: ClaimKind) -> Callable[..., Verdict]:
    """Return the resolver callable for the given ClaimKind."""
    return _DISPATCH[kind]


def _extract_constant_from_text(text: str) -> CuratedConstant | None:
    """Extract the constant name from claim text and return the CuratedConstant, or None."""
    import re

    from llmxive.verify import constants as _const
    from llmxive.verify.mode import _CONSTANT_NAMES, _SINGLE_LETTER_CONSTANTS

    lower = text.lower()
    # Try multi-word constant names first (longest match wins), then single-letter
    for name in sorted(_CONSTANT_NAMES, key=len, reverse=True):
        if name in _SINGLE_LETTER_CONSTANTS:
            if re.search(r"\b" + re.escape(name) + r"\b", lower):
                entry = _const.lookup(name)
                if entry is not None:
                    return entry
        else:
            if name in lower:
                entry = _const.lookup(name)
                if entry is not None:
                    return entry
    return None


def _resolve_approximate(claim: Claim, *, backend: Any, model: str | None,
                          repo_root: Path) -> Verdict | None:
    """Handle approximate mode claims (T010).

    Returns a Verdict if the constants table has a true value, else None
    (caller falls through to the normal kind dispatch).
    """
    from llmxive.verify import approximate as _approx

    text = claim.raw_text or claim.canonical or ""

    # Extract a recognized constant from the claim text
    const_entry = _extract_constant_from_text(text)
    if const_entry is None and claim.canonical and claim.canonical != text:
        const_entry = _extract_constant_from_text(claim.canonical)

    if const_entry is None:
        # No recognized constant → fall through to normal dispatch
        return None

    tv = const_entry.value

    # Parse the claimed value from the text
    try:
        spec = _approx.parse_precision(text)
    except ValueError:
        # Cannot parse a number → fall through
        return None

    hedge = _approx.has_hedge(text)

    if _approx.is_valid_rounding(spec.claimed, tv, decimals=spec.decimals, hedge=hedge):
        # Valid rounding — keep value as written (FR-007)
        # Format: integer-looking decimals (0) → no ".0"; otherwise fixed-point
        if spec.decimals == 0:
            _val_str = str(round(spec.claimed))
        else:
            _val_str = f"{spec.claimed:.{spec.decimals}f}"
        return Verdict(
            status=ClaimStatus.VERIFIED,
            value=_val_str,
            evidence={
                "mode": "approximate",
                "constant": const_entry.key if const_entry else None,
                "authority": const_entry.authority if const_entry else None,
                "url": const_entry.url if const_entry else None,
                "true_value": tv,
            },
            resolver="approximate",
        )
    else:
        # Invalid rounding → correct to properly rounded value
        corrected = _approx.correction(tv, decimals=spec.decimals)
        return Verdict(
            status=ClaimStatus.VERIFIED,
            value=corrected,
            evidence={
                "mode": "approximate",
                "corrected": True,
                "constant": const_entry.key if const_entry else None,
                "authority": const_entry.authority if const_entry else None,
                "url": const_entry.url if const_entry else None,
                "true_value": tv,
                "asserted": str(spec.claimed),
            },
            resolver="approximate",
        )


def _resolve_computational(claim: Claim, *, backend: Any, model: str | None,
                             repo_root: Path) -> Verdict | None:
    """Handle computational mode claims (T018).

    Returns a Verdict for verified/corrected claims, or None if not evaluable
    (caller falls through to normal kind dispatch).
    """
    from llmxive.verify import compute as _compute

    cv = _compute.verify_computational(claim, backend=backend, model=model,
                                        repo_root=repo_root)

    if cv.status == _compute.ComputeStatus.NOT_EVALUABLE:
        return None

    if cv.status == _compute.ComputeStatus.VERIFIED:
        return Verdict(
            status=ClaimStatus.VERIFIED,
            value=cv.asserted,
            evidence={
                "mode": "computational",
                "compute": {
                    "expression": cv.expression,
                    "computed": cv.computed,
                },
            },
            resolver="compute",
        )

    # REFUTED — the computed value IS the authority
    return Verdict(
        status=ClaimStatus.VERIFIED,
        value=cv.computed,
        evidence={
            "mode": "computational",
            "corrected": True,
            "compute": {
                "expression": cv.expression,
                "computed": cv.computed,
            },
            "asserted": cv.asserted,
        },
        resolver="compute",
    )


def resolve(claim: Claim, *, backend: Any, model: str | None,
            repo_root: Path) -> Verdict:
    """Dispatch to the correct resolver for ``claim.kind``.

    When LLMXIVE_CLAIM_FILL=1, first applies mode-based routing:
    - computational → verify_computational (sympy); not_evaluable falls through
    - approximate   → constants-table lookup + precision compare; no match falls through
    - else          → normal kind dispatch

    RESULT-kind claims never route to computational (they assert empirical results).

    Returns a :class:`Verdict` — never raises. On any unexpected error
    returns NOT_ENOUGH_INFO (fail-safe: absence of evidence ≠ verified).
    """
    if os.environ.get("LLMXIVE_CLAIM_FILL") == "1" and claim.kind != ClaimKind.RESULT:
        try:
            from llmxive.verify import mode as _mode
            m = _mode.select_mode(claim, backend=backend, model=model, repo_root=repo_root)

            if m == "computational":
                v = _resolve_computational(claim, backend=backend, model=model,
                                            repo_root=repo_root)
                if v is not None:
                    return v
                # not_evaluable → fall through to normal dispatch

            elif m == "approximate":
                v = _resolve_approximate(claim, backend=backend, model=model,
                                          repo_root=repo_root)
                if v is not None:
                    return v
                # no constant found → fall through to normal dispatch

        except Exception as exc:
            logger.warning("claims.resolve: mode routing failed for %s (%s: %s)",
                           claim.claim_id, type(exc).__name__, exc)
            # Fall through to normal dispatch

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
