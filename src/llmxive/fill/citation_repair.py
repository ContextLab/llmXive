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


def _find_value_span(text: str, value: str) -> tuple[int, int] | None:
    """Return (start, end) of the first occurrence of *value* in *text*, or None."""
    if not value:
        return None
    # Try exact match first
    idx = text.find(value)
    if idx != -1:
        return idx, idx + len(value)
    # Try case-insensitive
    m = re.search(re.escape(value), text, re.IGNORECASE)
    if m:
        return m.start(), m.end()
    return None


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
    if not value:
        return text

    # Idempotency: if the authoritative source is already cited, stop.
    if _already_has_authoritative(text, provenance):
        return text

    # Locate the value in the text
    span = _find_value_span(text, value)
    if span is None:
        # Value not in text — nothing to repair
        return text

    val_start, val_end = span
    win_start, win_end = _window(text, val_start, val_end)

    # Strip stale citations in the window
    cleaned = _strip_stale_citations_in_window(text, win_start, win_end)

    # After stripping, re-locate the value (the span may have shifted)
    new_span = _find_value_span(cleaned, value)
    if new_span is None:
        # Shouldn't happen, but be safe
        return cleaned

    _, new_val_end = new_span
    auth_citation = _authoritative_inline(provenance)

    # Append the authoritative citation right after the value
    # If there's already a space after the value, insert without doubling
    after = cleaned[new_val_end:new_val_end + 1]
    if after == " ":
        repaired = (
            cleaned[:new_val_end]
            + " "
            + auth_citation
            + cleaned[new_val_end + 1:]
        )
    else:
        repaired = (
            cleaned[:new_val_end]
            + " "
            + auth_citation
            + cleaned[new_val_end:]
        )

    return repaired


__all__ = ["repair_citation"]
