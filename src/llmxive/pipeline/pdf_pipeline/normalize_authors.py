"""Spec 009 FR-016: normalize author block to a canonical \\authorblock.

Rewrites the source's author/affiliation/email/ORCID macros to a single
canonical form rendered by the llmxive.cls \\authorblock macro.

Strategy:
    1. Extract \\author{...} content (which may contain inline newlines,
       email addresses, ORCID links, "thanks" footnotes, etc.).
    2. Extract \\affiliation{...} content (if present).
    3. Strip TeX cruft commonly leaking from arXiv preprints (\thanks{},
       \footnote{}, \and, \\\\ etc.) and produce a clean "Name1, Name2, ..."
       list plus an affiliation block.
    4. Replace the original \\author / \\affiliation calls with a single
       \\authorblock{<names>}{<affiliations>}{<emails or links>} call.

If no \\author macro is present the source is returned unchanged.
"""

from __future__ import annotations

import re

AUTHOR_RE = re.compile(r"\\author\{((?:[^{}]|\{[^{}]*\})*)\}", re.DOTALL)
AFFIL_RE = re.compile(r"\\affiliation\{((?:[^{}]|\{[^{}]*\})*)\}", re.DOTALL)
EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
ORCID_RE = re.compile(r"https?://orcid\.org/[\d\-X]+", re.IGNORECASE)


def _strip_thanks(s: str) -> str:
    # Strip \thanks{...} and \footnote{...} content
    s = re.sub(r"\\thanks\{[^{}]*\}", "", s)
    s = re.sub(r"\\footnote\{[^{}]*\}", "", s)
    return s


def _split_authors(author_block: str) -> list[str]:
    """Split a \\author{} body into individual author names."""
    s = _strip_thanks(author_block)
    # Common separators: \and, \\, comma-newline-and
    parts = re.split(r"\\and|\\\\|;\s*", s)
    out: list[str] = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip(" ,\n\t")
        # Trim trailing email if present
        p = re.sub(r"\s*<?[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+>?\s*$", "", p)
        # Trim trailing affiliation parens
        p = re.sub(r"\s*\([^)]*\)\s*$", "", p)
        # Trim trailing footnote markers like ^1, ^{1,2}
        p = re.sub(r"[\^\d{},]+$", "", p)
        if p:
            out.append(p.strip())
    return out


def normalize(src: str) -> str:
    """Replace \\author{...} (and optional \\affiliation{...}) with one \\authorblock{}{}{}."""
    am = AUTHOR_RE.search(src)
    if not am:
        return src

    raw_authors = am.group(1)
    authors = _split_authors(raw_authors)
    if not authors:
        return src

    aff_match = AFFIL_RE.search(src)
    affiliations = ""
    if aff_match:
        affiliations = re.sub(r"\s+", " ", _strip_thanks(aff_match.group(1))).strip()

    # Collect emails/ORCID links from anywhere in the author/affil block
    links: list[str] = []
    for pool in (raw_authors, aff_match.group(1) if aff_match else ""):
        links.extend(EMAIL_RE.findall(pool))
        links.extend(ORCID_RE.findall(pool))
    links = sorted(set(links))

    authorblock = (
        f"\\authorblock{{{', '.join(authors)}}}"
        f"{{{affiliations}}}"
        f"{{{', '.join(links)}}}"
    )

    # Use a callable replacement so backslash sequences in `authorblock`
    # (e.g. \a in \authorblock) aren't re-interpreted as regex escapes.
    new_src = AUTHOR_RE.sub(lambda _m: authorblock, src, count=1)
    if aff_match:
        new_src = AFFIL_RE.sub(lambda _m: "", new_src, count=1)
    return new_src
