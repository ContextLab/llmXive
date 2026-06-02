"""Derive the search subject from a claim (spec 017, fill-layer contract).

strip_asserted_value — PURE: removes the asserted value/number from raw text
                        while keeping subject, qualifiers, and context.
subject_query        — returns the search query string for a claim; falls back
                        to strip_asserted_value when no backend is supplied.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from llmxive.backends.router import reasoning_chat
from llmxive.claims.models import Claim


def strip_asserted_value(raw_text: str, value: str | None) -> str:
    """Remove the asserted *value* from *raw_text*, keeping subject+qualifiers.

    Handles comma-separated, space-separated, and plain digit-only variants of
    the number.  Strips surrounding whitespace artifacts left by the removal so
    the result reads cleanly.  Returns *raw_text* unchanged when *value* is
    None or empty.

    Examples
    --------
    >>> strip_asserted_value("27,635 prime knots at crossing number 13", "27635")
    'prime knots at crossing number 13'
    >>> strip_asserted_value("There are 9988 prime knots", "9988")
    'There are prime knots'
    """
    if not value:
        return raw_text

    # Normalise the value to its bare digits (strip commas/spaces the caller
    # may have included in the value string itself).
    bare = re.sub(r"[\s,]", "", value)

    if not bare.replace(".", "").isdigit() and "." not in bare:
        # Non-numeric value: do a plain substring removal (case-insensitive).
        pattern = re.compile(re.escape(value), re.IGNORECASE)
        cleaned = pattern.sub("", raw_text)
        return _tidy(cleaned)

    # Build a pattern that matches all human-formatted variants of the number:
    # * plain: 27635
    # * comma-thousands: 27,635
    # * space-thousands: 27 635
    #
    # Strategy: insert an optional separator (,| ) between every group of
    # digits as they appear in the bare number.  We split the bare digits into
    # chunks of at most 3 from the right (as in standard thousand-grouping) and
    # allow any mix of comma or space between them.
    variants = _build_number_variants(bare)
    pattern = re.compile(
        r"(?<!\d)(?:" + "|".join(re.escape(v) for v in variants) + r")(?!\d)"
    )
    cleaned = pattern.sub("", raw_text)
    return _tidy(cleaned)


def _build_number_variants(bare: str) -> list[str]:
    """Return the set of human-formatted variants for bare digits *bare*."""
    variants = {bare}
    # Only apply thousand-grouping to the integer part (before any decimal point)
    if "." in bare:
        int_part, dec_part = bare.split(".", 1)
    else:
        int_part, dec_part = bare, None

    # Group digits from the right in blocks of 3 (standard thousand separator)
    if len(int_part) > 3:
        groups: list[str] = []
        remaining = int_part
        while remaining:
            groups.insert(0, remaining[-3:])
            remaining = remaining[:-3]
        # Comma separator
        comma_fmt = ",".join(groups)
        # Space separator
        space_fmt = " ".join(groups)
        if dec_part is not None:
            comma_fmt += "." + dec_part
            space_fmt += "." + dec_part
        variants.add(comma_fmt)
        variants.add(space_fmt)

    # Also add the original value string in case it was already formatted
    return sorted(variants, key=len, reverse=True)  # longest first → greedy match


def _tidy(text: str) -> str:
    """Collapse multiple spaces / leading-trailing whitespace after removal."""
    # Replace runs of spaces (but not newlines) left by removals
    text = re.sub(r" {2,}", " ", text)
    # Remove orphan commas or punctuation left directly adjacent to spaces
    text = re.sub(r"\s+,\s+", " ", text)
    text = re.sub(r"^[,\s]+", "", text)
    text = re.sub(r"[,\s]+$", "", text)
    return text.strip()


# Stop-words excluded from the fact fingerprint so trivial rephrasings (which
# shuffle/insert function words) still collapse to the same subject token set.
_FINGERPRINT_STOP = frozenset({
    "the", "a", "an", "of", "in", "at", "to", "and", "or", "for", "by", "with",
    "there", "are", "is", "it", "its", "as", "on", "that", "this", "these",
    "those", "be", "been", "was", "were", "has", "have", "had", "number",
    "value", "count", "exact", "exactly", "total", "about", "approximately",
    "equals", "equal", "which", "whose", "from", "into", "per",
})


def _singularize(token: str) -> str:
    """Collapse a simple English plural to its singular stem (best-effort).

    Only used inside the fact fingerprint so that the convergence reviser's
    plural toggling ("crossings"↔"crossing", "knots"↔"knot") does not produce a
    new cache key.  Deliberately conservative — handles the common ``-ies`` and
    trailing ``-s`` cases on tokens long enough that the stem is still
    meaningful; leaves short tokens (``is`` already stop-worded, ``gas``) and
    ``-ss`` words (``class``, ``mass``) unchanged.  Mis-stemming is harmless for
    correctness: the numeric component of the fingerprint already separates
    different facts, so the worst case is a rare missed cache hit, never a
    wrong-fact collision.
    """
    if len(token) > 3 and token.endswith("ies"):
        return token[:-3] + "y"
    if (
        len(token) > 3
        and token.endswith("s")
        and not token.endswith("ss")
        and not token.endswith("us")
    ):
        return token[:-1]
    return token


def fact_fingerprint(
    claim: Claim,
    *,
    backend: Any = None,
    model: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Return a stable, rephrase-independent fingerprint of the FACT a claim asserts.

    The fingerprint is used as the fill verdict cache key so that the convergence
    reviser's per-round rephrasings of the SAME fact share one cache entry (which
    avoids re-resolving the same fact via arXiv/OEIS every round).

    Composition (deliberately number-aware):
      ``<sorted-numeric-tokens> | <sorted-subject-keywords>``

    Correctness — two DIFFERENT facts must NOT collide:
      * The *full set* of salient numeric tokens in the claim text is included
        (sorted), so a fact asserting 9988 and one asserting 27635 — or one
        qualified by "13 crossings" vs "12 crossings" — get different numeric
        components and therefore different fingerprints.
      * The subject keyword set is derived from :func:`subject_query` (the same
        deterministic subject extraction the search layer uses) with stop-words
        and digits stripped, so two facts about different subjects differ.
      * Only same-numbers + same-subject rephrasings collapse to one key.

    This function is PURE and deterministic when ``backend`` is ``None`` (the
    common cache-keying path); a backend is accepted only to mirror
    ``subject_query``'s signature and is not required.
    """
    raw = claim.raw_text or claim.canonical or ""

    # Numeric component: ALL salient numbers in the claim (sorted, bare digits).
    # Including the full set — not just the asserted value — keeps qualifier
    # numbers (e.g. the crossing index) part of the fact identity.
    bare_numbers = sorted({
        re.sub(r"[\s,_]", "", tok)
        for tok in re.findall(r"[-+]?\d[\d,_ ]*(?:\.\d+)?", raw)
    })
    num_part = " ".join(bare_numbers)

    # Subject component: subject keywords from the deterministic search query,
    # lower-cased, de-punctuated, stop-words + pure-digit tokens removed,
    # singular-normalized (so "crossings"/"crossing", "knots"/"knot" collapse —
    # the reviser freely toggles plurals between rounds), then sorted.
    subject = subject_query(claim, backend=None, model=None, repo_root=None)
    tokens = re.sub(r"[^a-z0-9 ]", " ", subject.lower()).split()
    keywords = sorted({
        _singularize(t)
        for t in tokens
        if t not in _FINGERPRINT_STOP and not t.isdigit() and len(t) > 1
    })
    subj_part = " ".join(keywords)

    return f"{num_part}|{subj_part}"


def subject_query(
    claim: Claim,
    *,
    backend: Any = None,
    model: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Return a search query string for *claim*.

    When *backend* is ``None`` (pure / offline), falls back to
    :func:`strip_asserted_value` applied to the claim's ``raw_text`` using
    ``resolved_value`` as the value to remove.  The resulting string contains
    the subject + qualifiers without the asserted number, which is exactly what
    a search engine needs.

    When *backend* is provided, an LLM call is made (Phase 3+); the pure
    fallback is still used if the LLM call fails or returns an empty string.
    """
    from llmxive.claims.models import ClaimKind

    raw = claim.raw_text or claim.canonical or ""

    # For RELATIONAL claims, the best search query is the object of the triple
    # (the entity whose property we want to look up, e.g. "Australia" for
    # "capital of Australia is Sydney").  Searching by the object gives Wikidata
    # a well-known entity name that it can resolve to a Q-id + property list.
    #
    # For MAGNITUDE claims, search by the subject category stripped of the
    # asserted extremum (e.g. "largest planet" → search "planet" or the full
    # superlative subject).
    if claim.kind == ClaimKind.RELATIONAL:
        try:
            from llmxive.claims.triple import decompose_triple
            subj, _rel, obj = decompose_triple(raw)
            # The object of the decomposed triple often contains both the
            # entity (e.g. "Australia") and the asserted value (e.g. "Sydney")
            # joined by "is".  Strip the asserted value to get the entity.
            # Pattern: "EntityName is AssertedValue" → "EntityName"
            obj_clean = re.split(r"\s+is\s+", obj, maxsplit=1)[0].strip()
            # If obj_clean is very short or same as the whole raw, use subj.
            candidate = obj_clean if obj_clean and len(obj_clean) > 1 else subj
            if candidate and candidate != raw:
                if backend is not None:
                    kw = _llm_keyword_query(raw, None, backend=backend, model=model)
                    if kw:
                        return kw
                return candidate.strip()
        except Exception:
            pass

    elif claim.kind == ClaimKind.MAGNITUDE:
        try:
            from llmxive.claims.triple import decompose_triple
            subj, _rel, obj = decompose_triple(raw)
            # The object is the asserted extremum (e.g. "Saturn"); the subject
            # carries the category (e.g. "the largest planet").
            # Strip the asserted object from the subject to get the category.
            category = re.sub(re.escape(obj), "", subj, flags=re.IGNORECASE).strip()
            category = _tidy(category)
            if category and len(category) > 2:
                # For MAGNITUDE, use the deterministic category directly.
                # LLM keyword queries tend to echo the full claim (e.g. "the
                # largest planet") which gives poor Wikipedia search recall;
                # the stripped category (e.g. "largest planet") is more
                # targeted.  We skip the LLM path here and rely on channel
                # fallback order (wikidata → wikipedia → paper) for recall.
                return category
        except Exception:
            pass

    # Deterministic baseline (also the offline fallback): strip the asserted
    # value + parenthetical citations. The value to strip is the one the CLAIM
    # ASSERTS (the to-be-corrected number), NOT ``resolved_value`` — at fill
    # time the claim is unresolved (NEI/REFUTED) so ``resolved_value`` is None.
    value = claim.resolved_value
    if not value:
        from llmxive.claims.resolve import _extract_number

        value = _extract_number(raw)
    baseline = _strip_parentheticals(strip_asserted_value(raw, value)).strip() or raw

    # With a backend, ask the LLM for a concise KEYWORD query. A
    # destuffed-sentence query poisons keyword search engines (e.g. Wikipedia
    # full-text ranks "the exact count is … at 13 crossings" against MH370 /
    # RMS Queen Mary); the salient noun phrase ("prime knots crossing number")
    # retrieves the right sources. This only affects search RECALL — the filled
    # value is still gated by present-in-source, so an LLM-chosen query can
    # never introduce an unsourced value.
    if backend is not None:
        kw = _llm_keyword_query(raw, value, backend=backend, model=model)
        if kw:
            return kw
    return baseline


def _llm_keyword_query(raw: str, value: str | None, *, backend: Any,
                       model: str | None) -> str | None:
    """Ask the LLM for a short keyword search query for the claim's subject,
    excluding the asserted value. Returns None on any failure (caller falls
    back to the deterministic baseline)."""
    from llmxive.backends.base import ChatMessage

    avoid = f' Do NOT include the number "{value}".' if value else ""
    prompt = (
        "Generate a concise web-search query (3 to 6 keywords) to look up the "
        "correct value for the SUBJECT of this factual claim. Output ONLY the "
        "keywords, no punctuation, no explanation." + avoid + f"\n\nClaim: {raw}"
    )
    try:
        resp = reasoning_chat(backend, [ChatMessage(role="user", content=prompt)], model=model)
        text = (getattr(resp, "text", None) or "").strip()
    except Exception:
        return None
    # Keep the first non-empty line; drop stray quotes/labels.
    line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    line = line.strip().strip('"').strip("'")
    line = re.sub(r"(?i)^(query|search)\s*[:=]\s*", "", line).strip()
    return line or None


def _strip_parentheticals(text: str) -> str:
    """Remove parenthetical/bracketed asides (citations) from a search query."""
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    return _tidy(text)


__all__ = ["fact_fingerprint", "strip_asserted_value", "subject_query"]
