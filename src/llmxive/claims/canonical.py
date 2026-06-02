"""Canonical, SUBJECT-keyed verified-fact store + correction sweep.

Closes a real trustworthiness gap in the claim layer (PROJ-552). The layer
resolves numeric claims PER-INSTANCE: the convergence reviser rephrases every
mention into a *new* claim each round, so the verified value (e.g. 9988 prime
knots at crossing number 13, from OEIS A002863) is established for *some*
mentions while a *different* mention that still asserts the fabricated 27,635
survives — verbatim — into the converged spec. The per-instance fill cache keys
on the asserted VALUE (numeric tokens included), so "9988…" and "27635…" hash
differently and it can never act as a subject→value lookup.

This module adds the missing layer:

``subject_key(claim)``
    A stable key for the claim's SUBJECT, EXCLUDING the asserted/verified value
    but INCLUDING qualifier numbers. "27,635 … crossing number 13" and
    "9,988 … crossing number 13" → the SAME key; "… crossing number 12" → a
    DIFFERENT key. A bare number / empty subject → "" (never canonical).

``build_canonical_facts(claims)``
    From VERIFIED claims that carry a ``resolved_value`` AND a fetched source,
    build ``subject_key -> CanonicalFact``. Agreeing duplicates collapse; a
    conflict keeps the first sourced/verified value and NEVER fabricates one.

``apply_canonical_corrections(text, facts)``
    Extract every numeric mention from ``text``; for each, compute its
    ``subject_key``; when ``facts`` has a fact for that subject AND the mention
    asserts a DIFFERENT value (digits-only), swap in the verified value
    (prose-preserving) and cite the verified source where it cleanly applies.
    CONSERVATIVE: corrects only on a confident, non-empty subject match with a
    differing value; never touches a number whose subject has no canonical fact.

PURE — no IO.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.claims.pointer import _digits_only, _render_numeric
from llmxive.fill.subject_query import (
    _FINGERPRINT_STOP,
    _singularize,
    _strip_parentheticals,
)

# Numeric token AS IT APPEARS in prose (keeps thousands separators + decimal).
# Identical grammar to claims/pointer._NUMBER_IN_TEXT_RE so the tokens we find
# here match the tokens the prose-preserving renderer swaps.
_NUMBER_IN_TEXT_RE = re.compile(
    r"[-+]?\d{1,3}(?:[,_]\d{3})+(?:\.\d+)?|[-+]?\d+(?:\.\d+)?"
)

# Citation-introducer phrases: text from any of these onward is a CITATION tail
# (author-year, page numbers, an OEIS A-number), NOT subject content. Cutting it
# keeps the subject key stable across the reviser's per-round citation
# rephrasings — "27,635 … as established in Hoste (1998)…" and
# "9,988 … (sequence A002863 in the OEIS)" share the same subject ("prime knots
# crossing number 13"). Anchored with a word boundary; matches to end-of-text.
_CITE_TAIL_RE = re.compile(
    r"(?i)\b(?:as\s+established\s+in|as\s+reported\s+in|as\s+shown\s+in|"
    r"as\s+established\s+by|according\s+to|established\s+(?:by|in)|"
    r"reported\s+(?:by|in)|shown\s+(?:by|in)|sequence)\b.*$"
)


def _subject_text(claim: Claim) -> str:
    """Subject prose for ``claim`` with citation noise removed.

    Strips parenthetical/bracketed asides (citations) and any trailing
    citation-introducer clause so only the noun phrase the number quantifies
    remains. PURE.
    """
    raw = claim.raw_text or claim.canonical or ""
    cleaned = _strip_parentheticals(raw)
    cleaned = _CITE_TAIL_RE.sub("", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# CanonicalFact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CanonicalFact:
    """A verified value for one subject, plus where it came from."""

    value: str
    source_id: str
    url: str
    quote: str


# ---------------------------------------------------------------------------
# subject_key
# ---------------------------------------------------------------------------


def _subject_keywords(claim: Claim) -> list[str]:
    """Sorted, rephrase-independent subject keywords (no digits).

    Uses the citation-stripped subject prose (:func:`_subject_text`) and the
    SAME normalisation as :func:`fill.subject_query.fact_fingerprint`:
    lower-cased, de-punctuated, stop-words + pure-digit tokens removed,
    singular-normalised (so the reviser's plural toggling collapses), sorted.
    """
    subject = _subject_text(claim)
    tokens = re.sub(r"[^a-z0-9 ]", " ", subject.lower()).split()
    return sorted({
        _singularize(t)
        for t in tokens
        if t not in _FINGERPRINT_STOP and not t.isdigit() and len(t) > 1
    })


def _qualifier_numbers(claim: Claim, *, exclude_digits: set[str]) -> list[str]:
    """Bare-digit numeric tokens in the SUBJECT prose that are not asserted values.

    The asserted value (the to-be-corrected number) and the verified value (the
    ``resolved_value``) are removed; what remains are *qualifier* numbers — the
    crossing index 13, a dimension — which are part of the subject's identity.
    Drawn from the citation-stripped :func:`_subject_text` so a citation's
    author-year / page numbers / OEIS A-number never enter the subject key.
    ``exclude_digits`` holds the digits-only forms to drop.
    """
    subject = _subject_text(claim)
    out: set[str] = set()
    for tok in re.findall(r"[-+]?\d[\d,_ ]*(?:\.\d+)?", subject):
        bare = re.sub(r"[\s,_]", "", tok)
        digits = _digits_only(bare)
        if not digits:
            continue
        if digits in exclude_digits:
            continue
        out.add(bare)
    return sorted(out)


def subject_key(claim: Claim) -> str:
    """Return a stable SUBJECT key for ``claim`` (asserted value excluded).

    Composition::

        <sorted qualifier-number tokens> | <sorted subject keywords>

    The asserted value (extracted from ``raw_text``) AND the ``resolved_value``
    digits are EXCLUDED from the numeric component, so two mentions of the same
    subject asserting different values share one key. Qualifier numbers (the
    crossing index, a year, …) are KEPT, so "… crossing number 13" and
    "… crossing number 12" differ. A claim with no distinctive subject content
    (empty keyword set) returns "" — it must never match anything.
    """
    # Digits to exclude from the numeric component: the resolved/verified value
    # and the originally-asserted value.
    exclude: set[str] = set()
    if claim.resolved_value:
        rv = _digits_only(claim.resolved_value)
        if rv:
            exclude.add(rv)
    asserted = _asserted_value(claim.raw_text or claim.canonical or "")
    if asserted:
        ad = _digits_only(asserted)
        if ad:
            exclude.add(ad)

    keywords = _subject_keywords(claim)
    if not keywords:
        # No distinctive subject → never a canonical fact (avoids matching a
        # bare number or an empty-subject claim against anything).
        return ""

    qualifiers = _qualifier_numbers(claim, exclude_digits=exclude)
    return f"{' '.join(qualifiers)}|{' '.join(keywords)}"


def _asserted_value(text: str) -> str | None:
    """The numeric token a mention ASSERTS (mirrors pointer._select_asserted_token).

    Prefers a token written with a thousands separator (the asserted magnitude in
    scientific prose conventionally carries grouping, while qualifiers/years do
    not); otherwise the first numeric token. Used both to exclude the asserted
    value from the subject key and to compare a mention's value against a fact.
    """
    matches: list[str] = _NUMBER_IN_TEXT_RE.findall(text)
    if not matches:
        return None
    for m in matches:
        if "," in m:
            return m
    return matches[0]


def _parse_key(key: str) -> tuple[frozenset[str], frozenset[str]]:
    """Split a ``subject_key`` into ``(qualifier-digit set, keyword set)``.

    Qualifiers are compared digits-only so ``13`` and a grouped variant collapse.
    """
    quals_part, _, kw_part = key.partition("|")
    quals = frozenset(_digits_only(q) for q in quals_part.split() if _digits_only(q))
    keywords = frozenset(k for k in kw_part.split() if k)
    return quals, keywords


def _subject_signature(claim: Claim) -> tuple[frozenset[str], frozenset[str]] | None:
    """A mention's ``(qualifier-digit set, keyword set)`` for containment matching.

    Returns None when the mention has no distinctive subject keywords (so a bare
    number can never match a canonical fact).
    """
    key = subject_key(claim)
    if not key:
        return None
    return _parse_key(key)


# ---------------------------------------------------------------------------
# build_canonical_facts
# ---------------------------------------------------------------------------


def _fetched_source(claim: Claim) -> tuple[str, str, str] | None:
    """Return ``(source_id, url, quote)`` for a VERIFIED claim with a real
    fetched fill source, or None when no source is attached.

    Reads the fill provenance the resolver stores in ``claim.evidence['fill']``
    (value/source_id/url/quote), the SAME shape ``service.py`` step 6 consumes.
    """
    ev = claim.evidence or {}
    fill = ev.get("fill") or {}
    source_id = str(fill.get("source_id") or "").strip()
    url = str(fill.get("url") or "").strip()
    quote = str(fill.get("quote") or "").strip()
    if not (source_id or url):
        return None
    return source_id, url, quote


def build_canonical_facts(claims: list[Claim]) -> dict[str, CanonicalFact]:
    """Map ``subject_key -> CanonicalFact`` for VERIFIED, sourced claims.

    Only VERIFIED claims with a ``resolved_value`` AND a fetched source
    contribute. Claims whose ``subject_key`` is "" are skipped. When the same
    subject_key recurs, the candidates should agree (all verified to the same
    value); if they DON'T, the first sourced/verified value is kept and the
    conflicting one is ignored — a verified value is NEVER fabricated or blended.
    """
    facts: dict[str, CanonicalFact] = {}
    for claim in claims:
        if claim.status != ClaimStatus.VERIFIED:
            continue
        if not claim.resolved_value:
            continue
        source = _fetched_source(claim)
        if source is None:
            continue
        key = subject_key(claim)
        if not key:
            continue
        source_id, url, quote = source
        candidate = CanonicalFact(
            value=str(claim.resolved_value),
            source_id=source_id,
            url=url,
            quote=quote,
        )
        existing = facts.get(key)
        if existing is None:
            facts[key] = candidate
            continue
        # Same subject already mapped. Agree → keep. Disagree → keep the first
        # (already sourced/verified); NEVER overwrite with a different value.
        if _digits_only(existing.value) == _digits_only(candidate.value):
            continue
        # Conflict: keep the first. (Both are VERIFIED+sourced here, so the
        # first-verified one wins deterministically; we never fabricate.)
    return facts


# ---------------------------------------------------------------------------
# apply_canonical_corrections
# ---------------------------------------------------------------------------

# A mention sentence is the prose chunk around a numeric token we use to build a
# throw-away Claim for subject keying. We segment on blank lines / sentence
# enders so a mention's qualifiers + subject travel with its number.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}|\n")


def _mention_claim(sentence: str) -> Claim:
    """Build a throw-away NUMERIC Claim for ``sentence`` so we can subject-key it.

    ``resolved_value`` is left None: the asserted value is excluded via
    :func:`subject_key`'s own ``_asserted_value`` extraction from ``raw_text``.
    """
    return Claim(
        claim_id="c_mention0",
        kind=ClaimKind.NUMERIC,
        raw_text=sentence,
        canonical=sentence,
        context="",
        artifact_path="",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="",
    )


def apply_canonical_corrections(
    text: str, facts: dict[str, CanonicalFact]
) -> tuple[str, list[dict[str, str]]]:
    """Force every mention of a verified subject to its verified value.

    Splits ``text`` into mention-sized chunks; for each chunk that contains a
    numeric token, computes its ``subject_key``. When ``facts`` has an entry for
    that subject AND the mention's asserted value differs from the verified value
    (compared digits-only), the asserted token is swapped for the verified value
    via the prose-preserving :func:`claims.pointer._render_numeric` (surrounding
    prose preserved byte-for-byte) and the verified source is cited where the
    citation machinery cleanly applies.

    CONSERVATIVE: a chunk is corrected ONLY on a confident, non-empty subject
    match with a differing value. Returns ``(corrected_text, corrections)``.
    """
    if not facts or not text:
        return text, []

    # Precompute each fact's subject SIGNATURE (qualifier-digit set, keyword set)
    # once. A mention is matched by CONTAINMENT (see :func:`_match_fact`), not by
    # exact key equality, so an incidental leading connective in the mention
    # ("And again, …") cannot defeat the sweep while the distinctive subject
    # terms + the qualifier number still gate the match.
    indexed: list[tuple[frozenset[str], frozenset[str], CanonicalFact]] = []
    for key, fact in facts.items():
        quals, keywords = _parse_key(key)
        if not keywords:
            continue
        indexed.append((quals, keywords, fact))

    corrections: list[dict[str, str]] = []
    out_parts: list[str] = []
    pos = 0
    # Walk the text preserving the exact separators between chunks: we rebuild
    # the string from (chunk, following-separator) pairs so whitespace/newlines
    # are byte-preserved.
    for m in _SENTENCE_SPLIT_RE.finditer(text):
        chunk = text[pos:m.start()]
        sep = m.group(0)
        out_parts.append(_correct_chunk(chunk, indexed, corrections))
        out_parts.append(sep)
        pos = m.end()
    # Trailing chunk after the last separator.
    out_parts.append(_correct_chunk(text[pos:], indexed, corrections))
    return "".join(out_parts), corrections


def _match_fact(
    claim: Claim,
    indexed: list[tuple[frozenset[str], frozenset[str], CanonicalFact]],
) -> tuple[CanonicalFact, frozenset[str]] | None:
    """Return ``(fact, fact-keywords)`` whose subject is contained in ``claim``'s.

    A fact matches when:
      * its qualifier-digit set EQUALS the mention's — the crossing index (or
        any other subject-defining number) must agree EXACTLY, so a fact for
        "crossing number 13" never corrects a "crossing number 12" mention, and
        a qualifier-LESS fact (e.g. a bare "prime knots → 49") only matches a
        qualifier-less mention (it can never silently overwrite a more specific,
        differently-qualified instance); AND
      * its keyword set is a SUBSET of the mention's — so an incidental leading
        connective ("And again, …") cannot defeat the match while every
        distinctive subject term is still required.
    When several facts match, the most specific (largest combined subject) wins;
    the match is abandoned as ambiguous if two equally-specific facts disagree
    on value (never fabricate / pick arbitrarily between conflicting subjects).
    The matched fact's keyword set is returned so the caller can enforce that the
    asserted number is ADJACENT to a subject keyword (it must quantify the noun).
    """
    sig = _subject_signature(claim)
    if sig is None:
        return None
    m_quals, m_keywords = sig
    candidates: list[tuple[int, CanonicalFact, frozenset[str]]] = []
    for f_quals, f_keywords, fact in indexed:
        if f_quals == m_quals and f_keywords <= m_keywords:
            candidates.append((len(f_quals) + len(f_keywords), fact, f_keywords))
    if not candidates:
        return None
    best_score = max(score for score, _f, _kw in candidates)
    best = [(fact, kw) for score, fact, kw in candidates if score == best_score]
    first_fact, first_kw = best[0]
    # Ambiguous only if equally-specific best matches disagree on value.
    if any(_digits_only(f.value) != _digits_only(first_fact.value) for f, _ in best[1:]):
        return None
    return first_fact, first_kw


# Tokenises the word immediately before / after a number so we can require the
# asserted count to be ADJACENT to a subject keyword (it must QUANTIFY the noun
# phrase, not merely co-occur with it in the sentence). A digits-glued token like
# "FR-001" → the preceding word "FR" is not a knot/prime keyword → rejected;
# "27,635 prime knots" → following word "prime" IS → accepted.
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z-]*")


def _adjacent_to_subject(
    text: str, start: int, end: int, keywords: frozenset[str]
) -> bool:
    """True when the number at ``text[start:end]`` is ADJACENT to a fact keyword.

    Examines the alphabetic word immediately PRECEDING and the one immediately
    FOLLOWING the number (singular-normalised, lower-cased), accepting the
    correction only when one of them is in ``keywords`` — i.e. the number truly
    quantifies the subject noun, rather than being an incidental number ("Phase
    1", "FR-001") in a sentence that merely mentions the subject. An EMPTY
    keyword set (a fact with no distinctive keywords — never built) accepts
    nothing. PURE.
    """
    if not keywords:
        return False
    neighbours: list[str] = []
    after = _WORD_RE.match(text[end:].lstrip())
    if after:
        neighbours.append(after.group(0))
    before_words = _WORD_RE.findall(text[:start])
    if before_words:
        neighbours.append(before_words[-1])
    for word in neighbours:
        if _singularize(word.lower()) in keywords:
            return True
    return False


def _correct_chunk(
    chunk: str,
    indexed: list[tuple[frozenset[str], frozenset[str], CanonicalFact]],
    corrections: list[dict[str, str]],
) -> str:
    """Correct a single mention chunk in place (prose-preserving) or return it
    unchanged when there is no confident, differing canonical match.

    Two passes, in order, both governed by the SAME conservative
    :func:`_match_fact` rule (qualifier set EQUAL + fact-keywords SUBSET):

    1. WHOLE-CHUNK match — keys the entire chunk's subject. Handles the isolated
       mention (one sentence whose qualifier set is exactly the fact's) and is
       the only pass that inserts an inline citation, so its prose/citation
       behaviour is byte-for-byte what it was before the local-window pass.
    2. LOCAL-WINDOW match — when (1) does not correct, scan EACH numeric token
       and key the TIGHT noun phrase around it (see :func:`_local_window`). This
       catches a fabricated value EMBEDDED in a number-dense sentence whose
       whole-chunk qualifier set (e.g. {11, 13, 1}) ≠ the fact's ({13}); the
       window keeps the qualifier set LOCAL to the phrase ({13}), so the match
       is exactly as conservative as the isolated case.
    """
    if not chunk or not _NUMBER_IN_TEXT_RE.search(chunk):
        return chunk
    # --- Pass 1: whole-chunk match (unchanged behaviour, incl. citation). ----
    claim = _mention_claim(chunk)
    matched = _match_fact(claim, indexed)
    if matched is not None:
        fact, f_keywords = matched
        asserted = _asserted_value(chunk)
        if (
            asserted is not None
            and _digits_only(asserted) != _digits_only(fact.value)
            and not _asserted_is_bound_or_percent(chunk, asserted)
            and _asserted_adjacent_to_subject(chunk, asserted, f_keywords)
        ):
            corrected = _render_numeric(chunk, fact.value)
            if corrected != chunk:
                corrected = _try_cite(corrected, claim, fact)
                corrections.append({
                    "subject_key": subject_key(claim),
                    "from": asserted,
                    "to": fact.value,
                    "source_id": fact.source_id,
                    "url": fact.url,
                })
                return corrected
    # --- Pass 2: local-window match for embedded, number-dense sentences. ----
    return _correct_local_windows(chunk, indexed, corrections)


def _asserted_adjacent_to_subject(
    chunk: str, asserted: str, keywords: frozenset[str]
) -> bool:
    """True when SOME occurrence of the asserted token in ``chunk`` is adjacent to
    a fact keyword (see :func:`_adjacent_to_subject`).

    The whole-chunk pass selects the asserted value as a string; an incidental
    number that merely co-occurs with the subject ("Phase 1", "FR-001") is never
    adjacent to a knot/prime keyword and is rejected. PURE.
    """
    digits = _digits_only(asserted)
    if not digits:
        return False
    for m in _NUMBER_IN_TEXT_RE.finditer(chunk):
        tok = m.group(0).rstrip()
        if _digits_only(tok) != digits:
            continue
        if _adjacent_to_subject(chunk, m.start(), m.start() + len(tok), keywords):
            return True
    return False


# A numeric token that is a BOUND (≤/≥/</>/~/≈ immediately before it) or a
# PERCENTAGE/ratio (``%`` immediately after it) is a threshold/proportion, NEVER
# the asserted COUNT a canonical knot-count fact describes. Correcting such a
# token would FABRICATE — e.g. rewriting "≥95% completeness" to a knot count, or
# "crossing number ≤10" (a crossing-index bound) to "≤49". These are skipped in
# BOTH passes so a count-fact can only ever overwrite an asserted count.
_BOUND_PREFIX = "≤≥<>~≈"


def _is_bound_or_percent(text: str, start: int, end: int) -> bool:
    """True when ``text[start:end]`` is a comparison BOUND or a PERCENTAGE.

    Bound: the char immediately before the number (skipping a sign) is one of
    ``≤ ≥ < > ~ ≈``. Percentage: the char immediately after is ``%``. PURE.
    """
    before = text[:start].rstrip("+-")
    if before and before[-1] in _BOUND_PREFIX:
        return True
    after = text[end:]
    return after[:1] == "%"


def _asserted_is_bound_or_percent(chunk: str, asserted: str) -> bool:
    """True when the asserted token (as selected for the whole-chunk pass) appears
    in ``chunk`` only as a bound/percentage occurrence.

    The whole-chunk pass selects the asserted value as a *string*; locate its
    occurrence(s) in ``chunk`` and, if EVERY occurrence is a bound/percentage,
    refuse the correction (it is a threshold, not a count). PURE.
    """
    digits = _digits_only(asserted)
    if not digits:
        return False
    occurrences = 0
    for m in _NUMBER_IN_TEXT_RE.finditer(chunk):
        tok = m.group(0).rstrip()
        if _digits_only(tok) != digits:
            continue
        occurrences += 1
        if not _is_bound_or_percent(chunk, m.start(), m.start() + len(tok)):
            return False  # at least one occurrence is a plain count → allow
    return occurrences > 0


# A clause boundary that terminates a number's LOCAL window. Forward: any of
# ``) , ; :`` or a sentence period, a newline, or a coordinating conjunction
# (` and `/` while `/` whereas `) — the noun phrase the number quantifies cannot
# run past these. (A decimal point inside a number is part of the numeric token,
# which we skip over before searching, so ``.`` here is always a clause period.)
# The window is FORWARD-ONLY: it starts AT the number and runs to this boundary,
# so the qualifier numbers it carries are exactly those of the local phrase
# (e.g. {13} from "prime knots at crossing number 13"), never the rest of a
# number-dense sentence — and never a preceding number that would pollute them.
_WINDOW_FWD_RE = re.compile(r"[),;:]|\.(?:\s|$)|\n|\s+(?:and|while|whereas)\s+", re.I)


def _local_window(text: str, start: int, end: int) -> str:
    """Return ``"<asserted-number> <local noun phrase>"`` for the token at
    ``text[start:end]``.

    The phrase is the text IMMEDIATELY FOLLOWING the number up to the nearest
    clause boundary (:data:`_WINDOW_FWD_RE`) — e.g. ``prime knots at crossing
    number 13`` from ``(27,635 prime knots at crossing number 13)``. The asserted
    number is placed FIRST so the synthetic claim's :func:`subject_key` excludes
    it as the asserted value while keeping ONLY the qualifier numbers LOCAL to
    this phrase (the trailing ``13``, not the whole sentence's {11, 13, 1}).
    PURE.
    """
    fwd = _WINDOW_FWD_RE.search(text, end)
    fwd_stop = fwd.start() if fwd else len(text)
    forward = text[end:fwd_stop]
    number = text[start:end]
    return f"{number} {forward}".strip()


def _correct_local_windows(
    chunk: str,
    indexed: list[tuple[frozenset[str], frozenset[str], CanonicalFact]],
    corrections: list[dict[str, str]],
) -> str:
    """Per-token local-window correction within ``chunk`` (prose-preserving).

    For every numeric token, build its local-window synthetic claim, match it
    against ``facts`` with the SAME conservative :func:`_match_fact` rule, and —
    on a confident match whose verified value DIFFERS — swap THAT token's exact
    occurrence for the verified value. Replacements are collected first and
    applied right-to-left so earlier character offsets stay valid; every other
    byte of ``chunk`` is preserved. Returns ``chunk`` unchanged when no token's
    local window confidently matches a differing fact.

    A token is corrected ONLY when it is the ASSERTED COUNT of its own window —
    i.e. it equals ``_asserted_value(window)`` — so a QUALIFIER number (the
    trailing ``13`` in "…crossing number 13", which the window keeps as a
    qualifier while ``27,635`` is the asserted value) is never itself rewritten
    to the fact value. As a second guard, a token whose digits appear in the
    matched fact's qualifier set is treated as a qualifier and skipped.
    """
    edits: list[tuple[int, int, str, dict[str, str]]] = []
    for m in _NUMBER_IN_TEXT_RE.finditer(chunk):
        token = m.group(0).rstrip()
        end = m.start() + len(token)
        token_digits = _digits_only(token)
        if not token_digits:
            continue
        # A bound (≤/≥/<…) or percentage (…%) is a threshold/proportion, never
        # an asserted count — never overwrite it with a count fact.
        if _is_bound_or_percent(chunk, m.start(), end):
            continue
        window = _local_window(chunk, m.start(), end)
        win_claim = _mention_claim(window)
        # The token must be the ASSERTED count of its own window, not a qualifier
        # (e.g. the trailing "13" in "…crossing number 13" is a qualifier and the
        # window's asserted value is the leading count — skip such tokens).
        asserted = _asserted_value(window)
        if asserted is None or _digits_only(asserted) != token_digits:
            continue
        matched = _match_fact(win_claim, indexed)
        if matched is None:
            continue
        fact, f_keywords = matched
        if token_digits == _digits_only(fact.value):
            continue  # already the verified value — leave byte-identical
        # The number must QUANTIFY the subject noun (adjacent to a fact keyword),
        # not merely co-occur with it in the dense sentence.
        if not _adjacent_to_subject(chunk, m.start(), end, f_keywords):
            continue
        # Defense in depth: never rewrite a number that IS a qualifier of the
        # matched fact (qualifier set is digits-only).
        f_quals, _f_keywords = _parse_key(subject_key(win_claim))
        if token_digits in f_quals:
            continue
        record = {
            "subject_key": subject_key(win_claim),
            "from": token,
            "to": fact.value,
            "source_id": fact.source_id,
            "url": fact.url,
        }
        edits.append((m.start(), end, fact.value, record))
    if not edits:
        return chunk
    # Apply right-to-left so each (start, end) span stays valid.
    out = chunk
    for start, end, value, record in sorted(edits, reverse=True):
        out = out[:start] + value + out[end:]
        corrections.append(record)
    return out


def _try_cite(text: str, claim: Claim, fact: CanonicalFact) -> str:
    """Best-effort: cite the verified fill source next to the corrected value."""
    try:
        from llmxive.fill.citation_repair import repair_citation
        from llmxive.fill.models import FillProvenance

        provenance = FillProvenance(
            value=fact.value,
            source_id=fact.source_id,
            url=fact.url,
            quote=fact.quote,
            channel=_channel_for(fact),
            conflicts=[],
        )
        # The corrected text now asserts the verified value; give the citation
        # repairer a claim whose raw_text carries that value so its anchor logic
        # locates the right sentence.
        anchor = Claim(
            claim_id=claim.claim_id,
            kind=ClaimKind.NUMERIC,
            raw_text=text,
            canonical=text,
            context=claim.context,
            artifact_path=claim.artifact_path,
            source_type="external",
            status=ClaimStatus.VERIFIED,
            resolved_value=fact.value,
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="",
        )
        cited = repair_citation(text, claim=anchor, provenance=provenance)
        if cited == text:
            return text
        # The citation repairer inserts ``(… )`` immediately after the value and
        # consumes the single space that separated the value from the following
        # word when the value is mid-sentence ("9988 (OEIS …)prime"). Restore
        # that lost separator so prose stays clean — we add ONLY the citation,
        # never garble surrounding text.
        return _restore_citation_separator(cited)
    except Exception:
        return text


# The inline citation our provenance produces ends with the source URL and a
# closing paren; when a word character butts directly against that paren, the
# separating space was consumed by the repairer — re-insert exactly one space.
_LOST_SEPARATOR_RE = re.compile(r"(https?://\S+\))(?=[A-Za-z0-9])")


def _restore_citation_separator(text: str) -> str:
    """Re-insert the single space the citation repairer consumed after ``(…url)``.

    Targets ONLY the lost-separator artifact at the end of an inserted inline
    citation (``…url)`` immediately followed by an alphanumeric). PURE.
    """
    return _LOST_SEPARATOR_RE.sub(r"\1 ", text)


def _channel_for(fact: CanonicalFact) -> str:
    """Infer the citation channel label from the source identity (best-effort)."""
    sid = (fact.source_id or "").strip()
    url = (fact.url or "").lower()
    if "oeis" in url or re.fullmatch(r"A\d{6,}", sid):
        return "oeis"
    if "wikidata" in url or re.fullmatch(r"Q\d+", sid):
        return "wikidata"
    if "wikipedia" in url:
        return "wikipedia"
    return ""


__all__ = [
    "CanonicalFact",
    "apply_canonical_corrections",
    "build_canonical_facts",
    "subject_key",
]
