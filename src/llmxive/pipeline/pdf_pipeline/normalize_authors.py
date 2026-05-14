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

EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")
ORCID_RE = re.compile(r"https?://orcid\.org/[\d\-X]+", re.IGNORECASE)


def _find_balanced(src: str, cmd: str) -> tuple[int, int, str] | None:
    """Find `\\cmd{...balanced...}` and return (start, end, content) or None.

    Regex-balanced-brace parsing doesn't work for arbitrary nesting; we
    walk braces by hand. Returns the OUTERMOST balanced span.
    """
    needle = "\\" + cmd + "{"
    idx = src.find(needle)
    if idx < 0:
        return None
    open_brace = idx + len(needle) - 1
    depth = 0
    i = open_brace
    while i < len(src):
        c = src[i]
        # respect \{ and \} as escaped braces
        if c == "\\" and i + 1 < len(src) and src[i + 1] in "{}":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return idx, i + 1, src[open_brace + 1:i]
        i += 1
    return None


def _strip_thanks(s: str) -> str:
    # Strip \thanks{...} and \footnote{...} content
    s = re.sub(r"\\thanks\{[^{}]*\}", "", s)
    s = re.sub(r"\\footnote\{[^{}]*\}", "", s)
    return s


def _strip_tex_decorations(s: str) -> str:
    """Strip TeX decorations that would create unbalanced braces in our authorblock.

    Iteration order matters: we strip `\\{` / `\\}` (escaped braces) FIRST,
    so subsequent `\\texttt{X}`-style strips see balanced `{...}` groups.
    """
    # Step 0: strip inline math $...$ FIRST — these contain braces that
    # would otherwise confuse the \textbf{X} / \texttt{X} matchers.
    s = re.sub(r"\$[^$]*\$", "", s)
    # Step 1: remove escaped braces (these are inside groups we'll later strip)
    s = s.replace(r"\{", "").replace(r"\}", "")
    # Step 2: \texttt{X}, \textbf{X}, etc. -> X (now with clean braces).
    # Iterate to handle nested cases.
    decorator_pat = re.compile(
        r"\\(?:texttt|textbf|textit|emph|textsuperscript|textsc|small|large|bfseries|itshape|rmfamily|sffamily|protect|ensuremath|mathit|mathbf)\s*\{([^{}]*)\}"
    )
    for _ in range(8):
        new_s = decorator_pat.sub(r"\1", s)
        if new_s == s:
            break
        s = new_s
    # Drop any leftover decorator commands that we couldn't unwrap
    # (e.g. \textbf{X{nested}Y} where stripping inner first leaves outer
    # mismatched). This is conservative: drop the macro name + its
    # opening { + immediate non-brace chars; the rest becomes plain text.
    s = re.sub(r"\\(?:texttt|textbf|textit|emph|textsuperscript|textsc|small|large|bfseries|itshape|rmfamily|sffamily|protect|ensuremath|mathit|mathbf)\b", "", s)
    # \href{url}{text} -> text
    s = re.sub(r"\\href\s*\{[^{}]*\}\s*\{([^{}]*)\}", r"\1", s)
    # \url{url} -> empty
    s = re.sub(r"\\url\s*\{[^{}]*\}", "", s)
    # \footnotemark[N], \footnotemark{N} -> empty
    s = re.sub(r"\\footnotemark\s*[\[\{][^\]\}]*[\]\}]", "", s)
    s = re.sub(r"\\footnotemark", "", s)
    # \and, \AND, \And separators replaced by ; for splitting
    s = re.sub(r"\\(?:AND|And|and)\b", ";", s)
    # Stray { } at this point likely from leftover commands — drop them
    s = s.replace("{", "").replace("}", "")
    return s


def _split_authors(author_block: str) -> list[str]:
    """Split a \\author{} body into individual author names."""
    s = _strip_thanks(author_block)
    s = _strip_tex_decorations(s)
    # Common separators: \and (already converted to ;), \\, ;
    parts = re.split(r"\\\\|;\s*", s)
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
    """Replace \\author{...} (and optional \\affiliation{...}) with one \\authorblock{}{}{}.

    Uses balanced-brace parsing (not regex) so arbitrarily-nested \\thanks{},
    \\footnotemark[], \\textsuperscript{}, multi-paragraph author blocks
    (NeurIPS / COLM / Springer-LNCS style) parse correctly.
    """
    found = _find_balanced(src, "author")
    if not found:
        return src
    au_start, au_end, raw_authors = found

    authors = _split_authors(raw_authors)
    if not authors:
        return src

    aff_found = _find_balanced(src, "affiliation")
    raw_affil = aff_found[2] if aff_found else ""
    affiliations = re.sub(r"\s+", " ", _strip_tex_decorations(_strip_thanks(raw_affil))).strip()

    # Collect emails/ORCID links from anywhere in the author/affil block
    links: list[str] = []
    for pool in (raw_authors, raw_affil):
        links.extend(EMAIL_RE.findall(pool))
        links.extend(ORCID_RE.findall(pool))
    links = sorted(set(links))

    authorblock = (
        f"\\authorblock{{{', '.join(authors)}}}"
        f"{{{affiliations}}}"
        f"{{{', '.join(links)}}}"
    )

    # Splice in the authorblock; remove the affiliation span if present.
    # Splice author first; recompute affil span (indices shift if author is
    # before affil).
    new_src = src[:au_start] + authorblock + src[au_end:]
    if aff_found:
        # Re-find affiliation in the spliced source — its position may have moved
        new_aff = _find_balanced(new_src, "affiliation")
        if new_aff:
            af_start, af_end, _ = new_aff
            new_src = new_src[:af_start] + new_src[af_end:]
    return new_src
