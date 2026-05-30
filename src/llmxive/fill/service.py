"""Fill service — top-level orchestrator for authoritative-fill (spec 017, T018).

fill_claim(claim, *, backend, model, repo_root) -> FillResult

Algorithm:
1. Guard: only NUMERIC and ENTITY_FACT claims are fillable in v1.
2. Build a search query via subject_query().
3. Invoke each channel in channels_for(kind, math=…) order.
4. Cross-channel OEIS enrichment: scan all fetched text + query + claim text
   for A-numbers; fetch b-files for any A-number not yet an OEIS source.
5. extract_value() (present-in-source gated) for each source.
6. choose() winner + conflict list → FillResult.filled / FillResult.blocked.
7. Cache the result by claim.canonical (best-effort).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from llmxive.claims.models import Claim, ClaimKind
from llmxive.fill.channels import AUTHORITY, channels_for
from llmxive.fill.channels import oeis as _oeis_mod
from llmxive.fill.conflict import choose
from llmxive.fill.extract import extract_value
from llmxive.fill.models import FetchedSource, FillProvenance, FillResult
from llmxive.fill.subject_query import subject_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Channel dispatch: name → search_and_fetch callable
# ---------------------------------------------------------------------------

def _get_channel(name: str):
    """Return the search_and_fetch function for the named channel."""
    if name == "constants":
        from llmxive.fill.channels import constants
        return constants.search_and_fetch
    if name == "oeis":
        from llmxive.fill.channels import oeis
        return oeis.search_and_fetch
    if name == "wikipedia":
        from llmxive.fill.channels import wikipedia
        return wikipedia.search_and_fetch
    if name == "paper":
        from llmxive.fill.channels import papers
        return papers.search_and_fetch
    if name == "theorem":
        from llmxive.fill.channels import theorem
        return theorem.search_and_fetch
    if name == "wikidata":
        # wikidata channel may not exist yet in v1; fail gracefully
        try:
            from llmxive.fill.channels import wikidata
            return wikidata.search_and_fetch
        except ImportError:
            return None
    return None


# ---------------------------------------------------------------------------
# Math classifier heuristic (gates the theorem channel)
# ---------------------------------------------------------------------------

_MATH_KEYWORDS_RE = re.compile(
    r"\b(theorem|proof|prime|knot|graph|topolog|homolog|manifold|integer|polynomial"
    r"|lattice|algebraic|analytic|eigenvalue|matrix|combinat|sequence|OEIS|A\d{6})\b",
    re.IGNORECASE,
)


def _is_math_claim(claim: Claim, *, backend: Any, model: str | None,
                   repo_root: Path | None) -> bool:
    """Return True if the claim looks like a math/theorem question.

    Tries the real math_classifier first; falls back to a lightweight regex
    heuristic if the classifier fails or no backend is available.
    """
    text = (claim.raw_text or claim.canonical or "")
    # Fast heuristic path (also used as fallback when classifier unavailable)
    heuristic = bool(_MATH_KEYWORDS_RE.search(text))

    if backend is None or repo_root is None:
        return heuristic

    try:
        from llmxive.librarian.math_classifier import classify
        result = classify(
            question=text,
            idea_body_excerpt=None,
            project_id=None,
            librarian_prompt_version="017",
            model=model or "qwen.qwen3.5-122b",
            default_backend=getattr(backend, "name", "dartmouth"),
            fallback_backends=["local"],
            repo_root=repo_root,
        )
        if result.verdict is not None:
            return bool(result.verdict)
    except Exception as exc:
        logger.debug("fill.service: math_classifier failed, using heuristic: %s", exc)

    return heuristic


# ---------------------------------------------------------------------------
# Cache helpers (reuse grounding/cache put_verdict / get_verdict)
# ---------------------------------------------------------------------------

def _cache_key_parts(claim: Claim) -> tuple[str, str, str | None]:
    """Return (source_id, claim_text, number) for grounding cache keying."""
    canonical = claim.canonical or claim.raw_text or ""
    return ("fill", canonical, claim.resolved_value)


def _load_cached(claim: Claim, *, repo_root: Path | None) -> FillResult | None:
    """Try to load a previously cached FillResult. Returns None on any miss/error."""
    if repo_root is None:
        return None
    try:
        from llmxive.grounding import cache as _cache
        source_id, canonical, number = _cache_key_parts(claim)
        data = _cache.get_verdict(repo_root, source_id=source_id, claim=canonical,
                                  number=number)
        if data is None:
            return None
        if data.get("status") == "filled":
            prov_d = data.get("provenance", {})
            prov = FillProvenance(
                value=prov_d.get("value", ""),
                source_id=prov_d.get("source_id", ""),
                url=prov_d.get("url", ""),
                quote=prov_d.get("quote", ""),
                channel=prov_d.get("channel", ""),
                conflicts=prov_d.get("conflicts", []),
            )
            return FillResult.filled(
                value=prov.value,
                provenance=prov,
                channels_tried=data.get("channels_tried", []),
            )
        if data.get("status") == "blocked":
            return FillResult.blocked(
                reason=data.get("reason", "cached blocked"),
                channels_tried=data.get("channels_tried", []),
            )
    except Exception as exc:
        logger.debug("fill.service: cache load failed: %s", exc)
    return None


def _store_cached(claim: Claim, result: FillResult, *, repo_root: Path | None) -> None:
    """Persist a FillResult in the grounding cache (best-effort)."""
    if repo_root is None:
        return
    try:
        from llmxive.grounding import cache as _cache
        source_id, canonical, number = _cache_key_parts(claim)
        if result.status == "filled":
            assert result.provenance is not None
            data = {
                "status": "filled",
                "provenance": result.provenance.to_dict(),
                "channels_tried": result.channels_tried,
            }
        else:
            data = {
                "status": "blocked",
                "reason": result.reason,
                "channels_tried": result.channels_tried,
            }
        _cache.put_verdict(repo_root, source_id=source_id, claim=canonical,
                           number=number, verdict=data)
    except Exception as exc:
        logger.debug("fill.service: cache store failed: %s", exc)


# ---------------------------------------------------------------------------
# OEIS cross-channel enrichment
# ---------------------------------------------------------------------------

def _oeis_enrich(
    sources: list[FetchedSource],
    claim: Claim,
    query: str,
    *,
    timeout: float = 30.0,
) -> list[FetchedSource]:
    """Scan claim text + query + RELEVANT fetched texts for A-numbers; fetch
    b-files for any A-number not already an OEIS source.

    Enrichment strategy (in priority order):
    1. A-numbers in the claim text itself or the query (always enriched).
    2. A-numbers in HIGHLY RELEVANT Wikipedia/paper sources — defined as sources
       whose text is short enough to be on-topic AND whose source_id or title
       contains a subject keyword from the query.

    We deliberately do NOT scan all fetched source texts (e.g. "500 (number)"
    wikipedia article mentioning A000124 is unrelated to prime knots).  This
    prevents cross-contamination from off-topic A-numbers reaching OEIS.
    """
    existing_oeis_ids = {s.source_id for s in sources if s.channel == "oeis"}

    # Step 1: A-numbers in claim text + query (highest confidence)
    primary_corpus = " ".join([
        query,
        claim.raw_text or "",
        claim.canonical or "",
    ])
    candidate_a_numbers: list[str] = list(_oeis_mod.a_numbers_in(primary_corpus))
    seen = set(candidate_a_numbers)

    # Step 2: A-numbers from topically relevant non-OEIS sources.
    # A source is "relevant" if its source_id/title contains a keyword from the
    # query (crude relevance gate: avoids completely off-topic pages).
    query_keywords = set(re.sub(r"[^a-z0-9 ]", " ", query.lower()).split())
    # Stop-words that add no topical signal
    _STOP = {"the", "a", "an", "of", "in", "at", "to", "and", "or", "for",
             "by", "with", "there", "are", "is", "it", "its"}
    query_keywords -= _STOP

    for src in sources:
        if src.channel == "oeis":
            continue
        # Check relevance: at least one query keyword in the source_id/title
        src_label = f"{src.source_id or ''} {src.title or ''}".lower()
        if not any(kw in src_label for kw in query_keywords):
            continue
        for a_num in _oeis_mod.a_numbers_in(src.text):
            if a_num not in seen:
                candidate_a_numbers.append(a_num)
                seen.add(a_num)

    new_sources: list[FetchedSource] = []
    for a_num in candidate_a_numbers:
        if a_num in existing_oeis_ids:
            continue
        try:
            data = _oeis_mod.fetch_bfile(a_num, timeout=timeout)
            if not data:
                continue
            text = _oeis_mod._render_bfile(data)
            if not text:
                continue
            new_sources.append(FetchedSource(
                channel="oeis",
                source_id=a_num,
                url=f"https://oeis.org/{a_num}",
                title=a_num,
                text=text,
                authority=AUTHORITY["oeis"],
            ))
            existing_oeis_ids.add(a_num)
        except Exception as exc:
            logger.debug("fill.service: OEIS enrich failed for %s: %s", a_num, exc)

    return sources + new_sources


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_FILLABLE_KINDS = {ClaimKind.NUMERIC, ClaimKind.ENTITY_FACT, ClaimKind.MAGNITUDE, ClaimKind.RELATIONAL}


def fill_claim(
    claim: Claim,
    *,
    backend: Any = None,
    model: str | None = None,
    repo_root: Path | None = None,
) -> FillResult:
    """Orchestrate the fill pipeline for one claim.

    Returns a FillResult (filled or blocked).  Never raises.
    """
    # Guard: only NUMERIC and ENTITY_FACT in v1
    if claim.kind not in _FILLABLE_KINDS:
        return FillResult.blocked(
            reason="claim kind not fillable in v1",
            channels_tried=[],
        )

    # Cache hit short-circuits the search
    cached = _load_cached(claim, repo_root=repo_root)
    if cached is not None:
        logger.debug("fill.service: cache hit for claim %s", claim.claim_id)
        return cached

    channels_tried: list[str] = []

    try:
        # Step 2: build search query
        q = subject_query(claim, backend=backend, model=model, repo_root=repo_root)

        # Step 3: determine math flag and channel list
        math = _is_math_claim(claim, backend=backend, model=model, repo_root=repo_root)
        channel_names = channels_for(claim.kind, math=math)

        # Gather all fetched sources across channels
        all_sources: list[FetchedSource] = []
        for ch_name in channel_names:
            fn = _get_channel(ch_name)
            if fn is None:
                logger.debug("fill.service: channel %r not available, skipping", ch_name)
                continue
            channels_tried.append(ch_name)
            try:
                fetched = fn(q, claim)
                all_sources.extend(fetched)
            except Exception as exc:
                logger.warning("fill.service: channel %r raised: %s", ch_name, exc)

        # Step 4: cross-channel OEIS enrichment
        all_sources = _oeis_enrich(all_sources, claim, q)
        # Ensure "oeis" is in channels_tried if we added OEIS sources from enrichment
        oeis_added = any(s.channel == "oeis" for s in all_sources)
        if oeis_added and "oeis" not in channels_tried:
            channels_tried.append("oeis")

        # Step 5: extract values (present-in-source gated inside extract_value)
        candidates: list[tuple[FetchedSource, str]] = []
        for source in all_sources:
            try:
                # Trim OEIS b-file sources to the relevant window so the LLM
                # locator stays within token budget.
                effective_source = _trim_oeis_source(source, claim)
                val = extract_value(
                    effective_source, claim,
                    backend=backend, model=model, repo_root=repo_root,
                )
                if val is not None:
                    # Record the win against the ORIGINAL (full) source for
                    # provenance (url/source_id are unchanged; only text differs).
                    candidates.append((source, val))
            except Exception as exc:
                logger.warning("fill.service: extract_value failed for %s: %s",
                               source.source_id, exc)

        # Step 6: no candidates → blocked
        if not candidates:
            result = FillResult.blocked(
                reason="value not present in any fetched source",
                channels_tried=channels_tried,
            )
            _store_cached(claim, result, repo_root=repo_root)
            return result

        # Step 7: choose winner via authority ranking
        winner_src, winner_val, conflicts = choose(candidates)

        # Build a quote: find the line in winner_src.text that contains the value
        quote = _find_quote(winner_val, winner_src.text)

        provenance = FillProvenance(
            value=winner_val,
            source_id=winner_src.source_id,
            url=winner_src.url,
            quote=quote,
            channel=winner_src.channel,
            conflicts=conflicts,
        )
        result = FillResult.filled(winner_val, provenance, channels_tried)
        _store_cached(claim, result, repo_root=repo_root)
        return result

    except Exception as exc:
        logger.warning("fill.service: unexpected error for claim %s: %s",
                       claim.claim_id, exc)
        return FillResult.blocked(
            reason=f"unexpected error: {type(exc).__name__}: {exc}",
            channels_tried=channels_tried,
        )


def _trim_oeis_source(source: FetchedSource, claim: Claim) -> FetchedSource:
    """Trim an OEIS b-file source to the window relevant to *claim*.

    OEIS b-files can be hundreds of lines long.  The LLM locator's token budget
    exhausts on large b-files.  When the claim mentions an explicit integer index
    (e.g. "at 13 crossings"), we narrow the b-file text to ±5 lines around that
    index.  The value at the target index is always included, so the trust
    boundary (value must be present in source.text) still holds.

    If no matching index is found or the source is not OEIS, returns *source*
    unchanged.
    """
    if source.channel != "oeis":
        return source

    # Extract a candidate index from the claim text (e.g. "13 crossings" → 13)
    import re
    # Look for patterns like "at N crossings", "N-crossing", "crossing N", etc.
    m = re.search(
        r"\b(\d{1,3})\s*(?:crossings?|crossing number|strands?|-crossing)\b"
        r"|(?:crossing(?:s)? number|at crossing)\s*(\d{1,3})\b",
        claim.raw_text or "", re.IGNORECASE
    )
    if not m:
        # Also try: plain integers that appear to be a small index
        nums = re.findall(r"\b([1-9]\d?)\b", claim.raw_text or "")
        if not nums:
            return source
        # Use the smallest reasonable index (likely the crossing number)
        try:
            idx = min(int(n) for n in nums if 1 <= int(n) <= 50)
        except ValueError:
            return source
    else:
        raw_idx = m.group(1) or m.group(2)
        try:
            idx = int(raw_idx)
        except (TypeError, ValueError):
            return source

    # Find the line with that index in the b-file text
    lines = source.text.splitlines()
    window: list[str] = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 1:
            try:
                line_idx = int(parts[0])
            except ValueError:
                continue
            if abs(line_idx - idx) <= 5:
                window.append(line)

    if not window:
        return source

    new_text = "\n".join(window)
    # Return a new FetchedSource with the trimmed text (same metadata)
    return FetchedSource(
        channel=source.channel,
        source_id=source.source_id,
        url=source.url,
        title=source.title,
        text=new_text,
        authority=source.authority,
    )


def _find_quote(value: str, text: str) -> str:
    """Return the first line in *text* that contains *value* (best-effort).

    Falls back to the value itself if no matching line is found.
    """
    bare = re.sub(r"[\s,]", "", value)
    for line in text.splitlines():
        # Check if value or its bare form appears in the line
        if value in line:
            return line.strip()
        if bare and bare in re.sub(r"[\s,]", "", line):
            return line.strip()
    return value


__all__ = ["fill_claim"]
