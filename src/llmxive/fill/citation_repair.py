"""Repair the citation adjacent to a filled claim's value (spec 017, FR-007, PURE).

repair_citation(text, *, claim, provenance) — rewrites/annotates the citation
    adjacent to the claim's value so the document cites the authoritative fill
    source; idempotent; leaves unrelated prose untouched.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from llmxive.claims.models import Claim
from llmxive.fill.models import FillProvenance

# ---------------------------------------------------------------------------
# Patterns for stale/free-text citation tokens near the claim value
# ---------------------------------------------------------------------------

# Matches a parenthesised citation block: (anything up to 120 chars)
_PAREN_CITATION_RE = re.compile(r"\(([^)]{1,120})\)")

# Matches arXiv references (possibly malformed — we want to strip them)
_ARXIV_RE = re.compile(r"\barXiv:\s*[\w./\-]+", re.IGNORECASE)

# Matches "Author et al. YYYY" style free-text citations
_AUTHOR_CITATION_RE = re.compile(r"\b[A-Z][a-z]+ et al\.\s*\d{4}[^)]*", re.IGNORECASE)

# Matches bare DOI tokens: doi:10.xxxx/yyyy or just 10.xxxx/yyyy
_BARE_DOI_RE = re.compile(r"(?:doi:\s*)?10\.\d{4,9}/\S+", re.IGNORECASE)

# Matches markdown links: [text](url)
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")

# How far (in characters) from the claim value we consider a citation "adjacent"
_ADJACENCY_WINDOW = 200


def _authoritative_citation(provenance: FillProvenance) -> str:
    """Build the inline authoritative citation string from *provenance*."""
    source_id = provenance.source_id
    url = provenance.url
    channel = provenance.channel

    # Human-readable channel label
    if channel == "oeis":
        label = f"OEIS {source_id}"
    elif channel == "wikidata":
        label = f"Wikidata {source_id}"
    elif channel == "wikipedia":
        label = f"Wikipedia: {source_id.replace('_', ' ')}"
    elif channel == "theorem":
        label = f"Theorem DB: {source_id}"
    else:
        label = source_id

    # Extract hostname for brevity
    try:
        host = urlparse(url).netloc
    except Exception:
        host = url

    return f"({label}, {host})"


def _authoritative_inline(provenance: FillProvenance) -> str:
    """Full inline citation including URL."""
    source_id = provenance.source_id
    url = provenance.url
    channel = provenance.channel

    if channel == "oeis":
        label = f"OEIS {source_id}"
    elif channel == "wikidata":
        label = f"Wikidata {source_id}"
    elif channel == "wikipedia":
        label = f"Wikipedia: {source_id.replace('_', ' ')}"
    elif channel == "theorem":
        label = f"Theorem DB: {source_id}"
    else:
        label = source_id

    return f"({label}, {url})"


def _already_has_authoritative(text: str, provenance: FillProvenance) -> bool:
    """Return True if *text* already contains the authoritative source reference."""
    return provenance.source_id in text and provenance.url in text


# Characters that, when adjacent to a numeric value, indicate the match is part
# of a larger number (so the value does not stand alone). Digits always do; a
# "." or "," only does when it sits between the value and another digit (e.g.
# "0.25", "1,296"), but here we conservatively treat any adjacent "."/"," as
# number-continuation to avoid splitting decimals/grouped numbers/dates.
_NUMBER_CONTINUATION = set("0123456789.,")

_DIGIT_RE = re.compile(r"\d")


def _is_numeric_value(value: str) -> bool:
    """True if *value* is a bare number (optionally with a single decimal sep)."""
    return bool(re.fullmatch(r"\d+(?:[.,]\d+)*", value))


def _boundary_valid(text: str, start: int, end: int, *, numeric: bool) -> bool:
    """Return True if the occurrence ``text[start:end]`` stands on its own.

    For numeric values the occurrence is invalid when the immediately preceding
    or following character is a digit, ``.`` or ``,`` (which would make the
    value part of a larger number such as ``2026``, ``0.25`` or ``1,296``).
    For non-numeric values we require a word boundary (the neighbour must not be
    an alphanumeric / underscore character).
    """
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    if numeric:
        if before in _NUMBER_CONTINUATION or after in _NUMBER_CONTINUATION:
            return False
        return True
    # Non-numeric: require word boundaries on both sides.
    if before and (before.isalnum() or before == "_"):
        return False
    if after and (after.isalnum() or after == "_"):
        return False
    return True


def _all_value_spans(text: str, value: str) -> list[tuple[int, int]]:
    """All boundary-valid occurrences of *value* in *text* (case-insensitive)."""
    if not value:
        return []
    numeric = _is_numeric_value(value)
    spans: list[tuple[int, int]] = []
    seen: set[int] = set()
    # Exact (case-sensitive) matches first, then case-insensitive, de-duplicated.
    for pattern, flags in ((re.escape(value), 0), (re.escape(value), re.IGNORECASE)):
        for m in re.finditer(pattern, text, flags):
            if m.start() in seen:
                continue
            if _boundary_valid(text, m.start(), m.end(), numeric=numeric):
                seen.add(m.start())
                spans.append((m.start(), m.end()))
    spans.sort()
    return spans


# Minimum length of a stable (non-numeric) anchor word taken from the claim's
# raw_text / canonical to locate the claim's own sentence in the document.
_MIN_ANCHOR_LEN = 4


def _anchor_words(claim: Claim) -> list[str]:
    """Distinctive non-numeric content words from the claim's text."""
    sources = [s for s in (claim.raw_text, claim.canonical) if s]
    words: list[str] = []
    seen_words: set[str] = set()
    for src in sources:
        for tok in re.findall(r"[A-Za-z][A-Za-z\-]+", src):
            key = tok.lower()
            # Skip short/common stop-like words; keep distinctive content words.
            if len(tok) < _MIN_ANCHOR_LEN or key in seen_words:
                continue
            if _DIGIT_RE.search(tok):
                continue
            seen_words.add(key)
            words.append(tok)
    return words


# A region is only treated as the claim's own sentence when it contains at least
# this many *distinct* anchor words — a single shared common word (e.g. "knot")
# appearing in unrelated prose is not a confident match.
_MIN_DISTINCT_ANCHORS = 2


def _anchor_regions(text: str, claim: Claim) -> list[tuple[int, int]]:
    """Return (start, end) spans in *text* where the claim's sentence appears.

    We anchor on distinctive *non-numeric* words drawn from the claim's
    ``raw_text``/``canonical`` (the numeric token may have been swapped at
    render time, but the surrounding words are stable). Each occurrence of such
    an anchor word contributes a hit; nearby hits are merged into regions, and
    only regions containing at least ``_MIN_DISTINCT_ANCHORS`` distinct anchor
    words are returned — so a lone common word in unrelated prose is ignored.

    When the claim has only one usable anchor word in total, that single word is
    sufficient (there is nothing more distinctive to require).
    """
    words = _anchor_words(claim)
    if not words:
        return []
    min_distinct = 1 if len(words) == 1 else _MIN_DISTINCT_ANCHORS

    # Collect (start, end, word_key) hits.
    hits: list[tuple[int, int, str]] = []
    for word in words:
        for m in re.finditer(re.escape(word), text, re.IGNORECASE):
            hits.append((m.start(), m.end(), word.lower()))
    if not hits:
        return []
    hits.sort()

    # Merge hits within the adjacency window into clusters, tracking distinct words.
    regions: list[tuple[int, int]] = []
    cur_start, cur_end, _key0 = hits[0]
    cur_keys = {hits[0][2]}
    for s, e, key in hits[1:]:
        if s - cur_end <= _ADJACENCY_WINDOW:
            cur_end = max(cur_end, e)
            cur_keys.add(key)
        else:
            if len(cur_keys) >= min_distinct:
                regions.append((cur_start, cur_end))
            cur_start, cur_end, cur_keys = s, e, {key}
    if len(cur_keys) >= min_distinct:
        regions.append((cur_start, cur_end))
    return regions


def _select_scoped_span(
    text: str, value: str, claim: Claim
) -> tuple[int, int] | None:
    """Pick the boundary-valid value occurrence inside the claim's sentence.

    Returns the chosen (start, end), or None when no occurrence can be
    *confidently* attributed to the claim (no anchor, no in-region occurrence,
    or an ambiguous choice) — in which case the caller must no-op.
    """
    spans = _all_value_spans(text, value)
    if not spans:
        return None

    regions = _anchor_regions(text, claim)
    if not regions:
        # No region matched the claim's sentence. If the claim has NO usable
        # anchor words at all, we cannot scope — fall back to a unique span only.
        # But if the claim HAS anchor words yet none located its sentence in the
        # document, the claim's sentence is absent → no-op (never cite an
        # unrelated standalone occurrence of the value).
        if _anchor_words(claim):
            return None
        if len(spans) == 1:
            return spans[0]
        return None

    # Collect occurrences that fall inside an anchor region.
    inside: list[tuple[int, int]] = []
    for s, e in spans:
        for r_start, r_end in regions:
            if s >= r_start and e <= r_end:
                inside.append((s, e))
                break
    if len(inside) == 1:
        return inside[0]
    if len(inside) > 1:
        # Multiple in-region candidates → ambiguous; no-op for safety.
        return None

    # No occurrence strictly inside a region: accept the single nearest span only
    # if it sits adjacent to (within the adjacency window of) exactly one region.
    near: list[tuple[int, int]] = []
    for s, e in spans:
        for r_start, r_end in regions:
            gap = max(r_start - e, s - r_end, 0)
            if gap <= _ADJACENCY_WINDOW:
                near.append((s, e))
                break
    if len(near) == 1:
        return near[0]
    return None


def _relocate_value(
    text: str, value: str, near_pos: int
) -> tuple[int, int] | None:
    """Find the boundary-valid occurrence of *value* closest to *near_pos*.

    Used after stale-citation stripping (which only removes characters within the
    adjacency window) to re-anchor on the *same* value occurrence we chose before.
    """
    spans = _all_value_spans(text, value)
    if not spans:
        return None
    return min(spans, key=lambda sp: abs(sp[0] - near_pos))


def _window(text: str, center_start: int, center_end: int) -> tuple[int, int]:
    """Return the (start, end) indices of the adjacency window around the value."""
    win_start = max(0, center_start - _ADJACENCY_WINDOW)
    win_end = min(len(text), center_end + _ADJACENCY_WINDOW)
    return win_start, win_end


def _strip_stale_citations_in_window(
    text: str, win_start: int, win_end: int
) -> str:
    """Remove stale citation tokens from the adjacency window only."""
    window = text[win_start:win_end]

    def _sub_in_window(pattern: re.Pattern[str], replacement: str, s: str) -> str:
        return pattern.sub(replacement, s)

    # Remove arXiv tokens
    window = _sub_in_window(_ARXIV_RE, "", window)
    # Remove bare DOI tokens
    window = _sub_in_window(_BARE_DOI_RE, "", window)
    # Remove markdown links (stale)
    window = _sub_in_window(_MD_LINK_RE, "", window)
    # Remove parenthesised blocks that contain stale citations
    def _strip_paren(m: re.Match[str]) -> str:
        inner = m.group(1)
        # Is this a stale citation block? Check for arXiv, DOI, "et al.", or URL
        if (
            re.search(r"arXiv:", inner, re.IGNORECASE)
            or re.search(r"10\.\d{4,9}/", inner)
            or re.search(r"et al\.", inner, re.IGNORECASE)
            or re.search(r"https?://", inner)
        ):
            return ""
        return str(m.group(0))  # leave non-citation parens intact

    window = _PAREN_CITATION_RE.sub(_strip_paren, window)

    # Tidy up double spaces left by removals
    window = re.sub(r" {2,}", " ", window).strip()

    return text[:win_start] + window + text[win_end:]


def repair_citation(text: str, *, claim: Claim, provenance: FillProvenance) -> str:
    """Rewrite/annotate the citation adjacent to the claim value.

    Algorithm:
    1. Locate the claim value in *text*.  If not found, return *text* unchanged.
    2. Check if the authoritative citation is already present (idempotency).
    3. Strip stale citation tokens (arXiv, DOI, markdown links, author-year) in
       the adjacency window around the value.
    4. Append the authoritative inline citation immediately after the value span.

    The function only modifies text within the adjacency window of the claim
    value — unrelated prose is never touched.
    """
    value = provenance.value or (claim.resolved_value or "")

    # spec 020 FR-007: the canonical stored form carries a durable {{claim:id}}
    # placeholder where the value would be (the value is substituted only in the
    # rendered view). When present it is an UNAMBIGUOUS single-occurrence anchor,
    # so repair the adjacent citation around it directly (no value scoping needed);
    # otherwise fall back to locating the value (legacy / rendered-view repair).
    # The citation is metadata and is corrected in the canonical stored form
    # exactly as before — only the anchor differs.
    from llmxive.claims.pointer import to_pointer

    placeholder = to_pointer(claim.claim_id)
    if placeholder in text:
        anchor = placeholder
        if _already_has_authoritative(text, provenance):
            return text
        p_start = text.index(placeholder)
        span: tuple[int, int] | None = (p_start, p_start + len(placeholder))
    else:
        anchor = value
        if not anchor:
            return text
        # Idempotency: if the authoritative source is already cited, stop.
        if _already_has_authoritative(text, provenance):
            return text
        # Locate the value in the text — boundary-aware and scoped to the claim's
        # own sentence. Returns None (→ no-op) when the choice is ambiguous or no
        # boundary-valid occurrence can be confidently attributed to the claim.
        span = _select_scoped_span(text, anchor, claim)
    if span is None:
        # Anchor not safely locatable — never garble unrelated prose.
        return text

    val_start, val_end = span
    win_start, win_end = _window(text, val_start, val_end)

    # Strip stale citations in the window
    cleaned = _strip_stale_citations_in_window(text, win_start, win_end)

    # After stripping, re-locate the value relative to the chosen span. Stripping
    # only edits inside [win_start, win_end] and only *removes* characters, so the
    # value position shifts by the number of chars removed before it within the
    # window. Re-select against the cleaned text, preferring the occurrence
    # nearest the original (boundary-valid) position.
    new_span = _relocate_value(cleaned, anchor, val_start)
    if new_span is None:
        # Shouldn't happen, but be safe
        return cleaned

    _, new_val_end = new_span
    auth_citation = _authoritative_inline(provenance)

    # Append the authoritative citation right after the value, with a single
    # space on EACH side. The char that followed the value (a space, punctuation,
    # or — rarely — a letter) now follows the citation; when that follower is
    # alphanumeric we insert a separating space so the citation never abuts the
    # next word (e.g. "9988 (OEIS A002863) prime", NOT the lost-separator
    # "9988 (OEIS A002863)prime"). ``cleaned[:new_val_end]`` ends at the value
    # (no trailing space), so the leading " " never doubles.
    tail = cleaned[new_val_end:]
    if tail[:1].isalnum():
        tail = " " + tail
    repaired = cleaned[:new_val_end] + " " + auth_citation + tail

    return repaired


__all__ = ["repair_citation"]
