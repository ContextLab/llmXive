#!/usr/bin/env python3
"""Extract the *content* of an arXiv-style LaTeX paper into a fresh,
self-contained wrapper that loads `llmxive.cls` and nothing venue-specific.

The strategy (per user request: "really we just need to strip out the text
+ figures … can we generate some sort of AST like version of the tex …
and simply remove any custom class-specific commands"):

  1. Recursively inline every `\\input{...}` and `\\include{...}` into one
     self-contained TeX string so we don't depend on the source tree's
     module layout.
  2. Walk the resulting LaTeX with `pylatexenc`'s LatexWalker — a real
     LaTeX tokenizer — to locate the `\\begin{document}` ... `\\end{document}`
     span. Only the body matters; the original preamble is discarded
     entirely.
  3. From the body, capture the title / author / date / abstract / keywords
     blocks for transplant into the llmxive wrapper's preamble.
  4. Emit a fresh wrapper that:
       - loads `\\documentclass{llmxive}`
       - emits a small **shim** layer that `\\providecommand`s every
         venue-specific macro the body uses (e.g. `\\correspondingauthor`,
         `\\todo`, `\\affiliation`, `\\runningtitle`, …) as a no-op or sane
         default so unknown macros don't break the compile
       - includes the inlined body between its own `\\begin{document}` /
         `\\end{document}`
       - keeps the original `\\bibliography{...}` and bib style verbatim
         (the .bib files travel alongside the source dir, so bibtex works)

Why this is safer than the old approach:
  - We never `\\input{preamble}` again — the original preamble's package
    pile-ups, conflicting `\\renewcommand`s, and bundled `.cls` references
    can't poison our build.
  - Unknown commands in the body get a no-op shim, so the compile keeps
    going rather than hard-failing at the first `Undefined control sequence`.

This is fundamentally a heuristic; we cannot perfectly emulate every TeX
preamble's intent. But the goal here is "compile cleanly to llmxive
style for the vast majority of well-formed arXiv submissions," not
bit-for-bit fidelity. When something does fail, `compile_paper.py` falls
back to the canonical arXiv PDF.

CLI:
  python scripts/extract_paper_content.py <source_dir> <entry.tex> \\
      --arxiv-id <id> --out main-llmxive.tex
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from pylatexenc.latexwalker import (
        LatexWalker, LatexEnvironmentNode, LatexMacroNode, LatexCommentNode,
    )
except ImportError:
    LatexWalker = None  # type: ignore


# ───────────────────────────────────────────────────────────────────────
# 1. Recursive \input / \include resolution
# ───────────────────────────────────────────────────────────────────────

_INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")


def _resolve_tex(src_root: Path, entry: Path, *,
                 _seen: set[Path] | None = None,
                 _depth: int = 0,
                 _max_depth: int = 8) -> str:
    """Recursively inline `\\input{X}` and `\\include{X}` into one TeX
    string. Cycles + missing files are passed through as comments so
    nothing silently disappears.
    """
    if _seen is None:
        _seen = set()
    entry = entry.resolve()
    if entry in _seen or _depth > _max_depth:
        return f"% [llmxive-extract] dropped recursive/deep input: {entry.name}\n"
    if not entry.is_file():
        # Try with .tex appended
        with_ext = entry.with_suffix(".tex")
        if with_ext.is_file():
            entry = with_ext
        else:
            return f"% [llmxive-extract] missing input: {entry.name}\n"
    _seen.add(entry)
    text = entry.read_text(encoding="utf-8", errors="replace")

    def _repl(m: re.Match[str]) -> str:
        target = m.group(1).strip()
        # \input{} can omit the extension; LaTeX adds .tex
        cand = src_root / target
        if not cand.is_file():
            cand = src_root / (target + ".tex")
        if not cand.is_file():
            return f"% [llmxive-extract] missing input: {target}\n"
        return _resolve_tex(src_root, cand, _seen=_seen, _depth=_depth + 1,
                            _max_depth=_max_depth)

    return _INPUT_RE.sub(_repl, text)


# ───────────────────────────────────────────────────────────────────────
# 2. Locate the document body
# ───────────────────────────────────────────────────────────────────────

_BEGIN_DOC = re.compile(r"\\begin\s*\{document\}")
_END_DOC = re.compile(r"\\end\s*\{document\}")


def _slice_document(tex: str) -> tuple[str, str]:
    """Return (preamble, body) split at \\begin{document}/\\end{document}."""
    bm = _BEGIN_DOC.search(tex)
    em = _END_DOC.search(tex, bm.end() if bm else 0)
    if not bm or not em:
        # No document boundaries — caller will report this as a parse error.
        return tex, ""
    return tex[: bm.start()], tex[bm.end(): em.start()]


# ───────────────────────────────────────────────────────────────────────
# 3. Capture title / author / date / abstract / keywords from preamble + body
# ───────────────────────────────────────────────────────────────────────

# Simple regex-based extractors — the AST walker would be more precise but
# these blocks are nearly always at the top of either the preamble or the
# body, and braces are unambiguously balanced in well-formed TeX.

def _capture_braced_arg(tex: str, after_idx: int) -> tuple[str | None, int]:
    """Starting at `after_idx`, skip whitespace then capture the next
    brace-balanced argument. Returns (content_or_None, end_idx_after_close).
    """
    i = after_idx
    n = len(tex)
    while i < n and tex[i] in " \t\r\n":
        i += 1
    if i >= n or tex[i] != "{":
        return None, after_idx
    depth = 1
    i += 1
    start = i
    while i < n and depth > 0:
        c = tex[i]
        if c == "\\" and i + 1 < n:
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return tex[start:i], i + 1
        i += 1
    return None, after_idx


def _strip_tex_comments(tex: str) -> str:
    """Remove `%`-comments from a TeX string, preserving `\\%` literals.

    LaTeX defines `%` as the start-of-comment character; everything from
    `%` to the end of the line (plus the newline) is dropped. `\\%` is
    a literal percent, NOT a comment marker. This matters for our
    `_extract_macro` calls: `\\title{}` mentioned inside a `% Note: ...`
    block would otherwise look like an empty real \\title to the regex.
    """
    out = []
    n = len(tex)
    i = 0
    while i < n:
        c = tex[i]
        if c == "\\" and i + 1 < n:
            # backslash + next char (escape) — never start a comment
            out.append(tex[i : i + 2])
            i += 2
            continue
        if c == "%":
            # skip to end of line (and the newline itself per TeX rules)
            eol = tex.find("\n", i)
            if eol == -1:
                break  # rest is comment
            i = eol + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _extract_macro(tex: str, macro: str) -> str | None:
    """First brace-balanced argument to `\\macro{...}` whose content
    is non-empty (or None). Comments are stripped first so `\\title{}`
    inside a `% Note ...` block doesn't mask a later real `\\title{...}`.
    Empty-argument matches are skipped — they almost always mean the
    `\\macro{}` token appeared in a comment about how to use the macro.

    Skips an optional `[...]` arg between the macro and the braced arg
    (the `authblk` style `\\author[1,2]{Name}` puts the affiliation key
    in brackets before the name; without this skip, PROJ-575 and similar
    multi-author papers parse no authors at all).
    """
    stripped = _strip_tex_comments(tex)
    for m in re.finditer(r"\\" + macro + r"\b", stripped):
        cursor = m.end()
        # Skip optional [..] arg before the mandatory {..}
        bracket_m = re.match(r"\s*\[[^\]]*\]", stripped[cursor:])
        if bracket_m:
            cursor += bracket_m.end()
        arg, _ = _capture_braced_arg(stripped, cursor)
        if arg and arg.strip():
            return arg
    return None


def _extract_all_macros(tex: str, macro: str) -> list[str]:
    """Every brace-balanced argument to `\\macro{...}` (in source order).

    Used for the authblk-style shape where each author is its own
    `\\author[K]{Name}` call. Single-`\\author{All \\and Authors}` papers
    produce a single-element list. Empty args are skipped.
    """
    stripped = _strip_tex_comments(tex)
    out: list[str] = []
    for m in re.finditer(r"\\" + macro + r"\b", stripped):
        cursor = m.end()
        bracket_m = re.match(r"\s*\[[^\]]*\]", stripped[cursor:])
        if bracket_m:
            cursor += bracket_m.end()
        arg, _ = _capture_braced_arg(stripped, cursor)
        if arg and arg.strip():
            out.append(arg.strip())
    return out


def _extract_env(tex: str, env: str) -> str | None:
    """Body of the first `\\begin{env}...\\end{env}` block (or None)."""
    m = re.search(r"\\begin\s*\{" + env + r"\}", tex)
    if not m:
        return None
    em = re.search(r"\\end\s*\{" + env + r"\}", tex[m.end():])
    if not em:
        return None
    return tex[m.end(): m.end() + em.start()].strip()


# ───────────────────────────────────────────────────────────────────────
# 4. Strip body-side commands that belong to the original class
# ───────────────────────────────────────────────────────────────────────

# Commands we drop from the body entirely (the wrapper preamble re-emits
# title/author/etc. via the llmxive class's own mechanisms).
_BODY_DROP_COMMANDS = {
    "maketitle", "titlerunning", "authorrunning",
    "institute", "address", "affiliation",
    "correspondingauthor", "thanks",
    # Venue-specific title/author/affiliation machinery that we've
    # already captured via the title/author aliases above; leaving these
    # in the body would re-invoke them with arguments that the llmxive
    # class doesn't understand.
    "icmltitle", "icmltitlerunning",
    "icmlauthor", "icmlsetsymbol",
    "icmlaffiliation", "icmlcorrespondingauthor",
    "icmlkeywords",
    "printAffiliationsAndNotice",
}

# Environments to drop from the body (similar reasoning).
_BODY_DROP_ENVS = {"icmlauthorlist"}


def _strip_body_commands(body: str) -> str:
    """Remove commands whose arguments we've already captured for the
    wrapper preamble. Each is removed along with its (possibly empty)
    brace-balanced argument. Also strips `_BODY_DROP_ENVS` environments
    in their entirety (no partial fragments left behind).
    """
    # First pass: drop whole environments in _BODY_DROP_ENVS.
    for env in _BODY_DROP_ENVS:
        body = re.sub(
            r"\\begin\s*\{" + env + r"\}.*?\\end\s*\{" + env + r"\}",
            "", body, flags=re.S,
        )
    # Second pass: strip drop-list macros + their arg.
    out = []
    i = 0
    n = len(body)
    while i < n:
        if body[i] == "\\":
            m = re.match(r"\\([A-Za-z]+)\*?", body[i:])
            if m and m.group(1) in _BODY_DROP_COMMANDS:
                after = i + m.end()
                _, after = _capture_braced_arg(body, after)
                i = after
                continue
        out.append(body[i])
        i += 1
    return "".join(out)


# ───────────────────────────────────────────────────────────────────────
# 5. Discover unknown macros that need shims
# ───────────────────────────────────────────────────────────────────────

# These are venue/template-specific commands we sometimes see in arXiv
# submissions. We `\providecommand` each one in the wrapper so unknown
# macros in the body don't crash the build. Each is a low-fidelity shim:
# we keep the text, drop the formatting.
_KNOWN_SHIMS: dict[str, str] = {
    # common formatting/aux macros (NAME → \providecommand body)
    "todo":             r"\providecommand{\todo}[1]{}",
    "TODO":             r"\providecommand{\TODO}[1]{}",
    "eg":               r"\providecommand{\eg}{e.g.,\xspace}",
    "ie":               r"\providecommand{\ie}{i.e.,\xspace}",
    "etal":             r"\providecommand{\etal}{et al.\xspace}",
    "etc":              r"\providecommand{\etc}{etc.\xspace}",
    "wrt":              r"\providecommand{\wrt}{w.r.t.\xspace}",
    "iid":              r"\providecommand{\iid}{i.i.d.\xspace}",
    # bracketed alternates from a few labs
    "correspondingauthor": r"\providecommand{\correspondingauthor}[1]{}",
    "affiliation":         r"\providecommand{\affiliation}[1]{}",
    "titlerunning":        r"\providecommand{\titlerunning}[1]{}",
    "authorrunning":       r"\providecommand{\authorrunning}[1]{}",
    "institute":           r"\providecommand{\institute}[1]{}",
    "address":             r"\providecommand{\address}[1]{}",
    "email":               r"\providecommand{\email}[1]{\href{mailto:#1}{#1}}",
    "keywords":            r"\providecommand{\keywords}[1]{\par\noindent\textbf{Keywords:} #1}",
    # `\and` is defined by article/report classes to work ONLY inside
    # \author / \date / \title. Outside those, it can cause \crcr / \cr
    # errors (it expands to alignment material). Re-providing as " · "
    # makes it safe in any context (e.g. \keywords{ A \and B \and C }).
    "and":                 r"\providecommand{\and}{ \textperiodcentered\ }",
    # Math helpers seen frequently
    "argmax":              r"\providecommand{\argmax}{\mathop{\mathrm{arg\,max}}}",
    "argmin":              r"\providecommand{\argmin}{\mathop{\mathrm{arg\,min}}}",
    # NeurIPS / ICML / CVPR styles often define these
    "iclrfinalcopy":       r"\providecommand{\iclrfinalcopy}{}",
    "neuripsfinalcopy":    r"\providecommand{\neuripsfinalcopy}{}",
    "icmlfinalcopy":       r"\providecommand{\icmlfinalcopy}{}",
    "aistatsfinalcopy":    r"\providecommand{\aistatsfinalcopy}{}",
    # acknowledgments environments
    "acknowledgments":     r"\providecommand{\acknowledgments}{\section*{Acknowledgments}}",
    # \blfootnote — "blank footnote" (no number) used for equal-contribution
    # or corresponding-author footnotes on the title page. The canonical
    # definition rewrites \@thefnmark to nothing; without a shim, the
    # body's \blfootnote{*Equal contribution.} bombs with `Use of \@
    # doesn't match its definition` (PROJ-569 — InternAtlas paper used
    # this for its equal-contribution authors).
    # Render as a regular footnote (loses the no-number distinction but
    # keeps the content visible — which is what the user wants).
    "blfootnote":          r"\providecommand{\blfootnote}[1]{\footnote{#1}}",
    # Misc author/affiliation shims that papers from major labs ship
    # custom-defined and then rely on through the body.
    "equalcontribution":   r"\providecommand{\equalcontribution}{}",
    "corresponding":       r"\providecommand{\corresponding}{}",
    # `\animategraphics[<opts>]{<fps>}{<basename>}{<first>}{<last>}` from
    # the animate package — papers shipping click-to-play video figures
    # (PROJ-567 AnyFlow teaser) embed this. We don't load animate (it's
    # heavy and rarely needed for static PDFs), so render the FIRST
    # frame as a static image instead. The trailing-`}` swallow keeps
    # animate's optional [poster=...] arguments from confusing parsers.
    "animategraphics":     r"\providecommand{\animategraphics}[5][]{\includegraphics[#1]{#3#4}}",
    # `\tablecite` — some authors define a table-only citation style
    # (e.g. shorter or unsuperscripted). Render as a normal \cite so
    # the bibliography reference still resolves.
    "tablecite":           r"\providecommand{\tablecite}[1]{\cite{#1}}",
    "footnotemark":        r"",  # placeholder: do NOT shim — it's a real LaTeX builtin
}
# Remove the placeholder we use to comment a NOT-shim — keeping the dict
# clean is more important than a one-line comment.
_KNOWN_SHIMS.pop("footnotemark", None)


# Macros where `\providecommand` is NOT enough — these are already
# defined either by article.cls (e.g. \and, \thanks) or by the llmxive
# class (e.g. \keywords). For these we use `\AtBeginDocument` +
# `\renewcommand` so the override fires AFTER all classes have loaded.
_FORCED_REDEF_NAMES = {"and", "thanks"}


def _shim_block() -> str:
    """All shims, in a single \\makeatletter/\\makeatother block.

    Most shims use `\\providecommand` (no-op if the macro already exists).
    A small set in `_FORCED_REDEF_NAMES` use `\\AtBeginDocument` +
    `\\renewcommand` because LaTeX's standard classes already define
    them (and would crash with the venue's behavior intact).
    """
    lines = [r"\makeatletter"]
    forced_lines = []
    for name, line in sorted(_KNOWN_SHIMS.items()):
        if name in _FORCED_REDEF_NAMES:
            # Convert "\providecommand{\and}{..." → "\renewcommand{\and}{..."
            renew = line.replace(r"\providecommand", r"\renewcommand", 1)
            forced_lines.append(rf"\AtBeginDocument{{{renew}}}")
        else:
            lines.append(line)
    lines.extend(forced_lines)
    lines.append(r"\makeatother")
    return "\n".join(lines)


# ───────────────────────────────────────────────────────────────────────
# 6. Extract package directives we DO want to keep
# ───────────────────────────────────────────────────────────────────────

# Packages safe to forward from the original preamble (the llmxive class
# does NOT load these by default). Anything not listed is dropped.
_SAFE_FORWARD_PACKAGES = {
    "amsmath", "amssymb", "amsfonts", "amsthm", "mathtools", "bm",
    "natbib", "biblatex",      # bibliography styles
    "algorithm", "algorithmic", "algorithm2e", "algpseudocode",
    "subcaption", "subfig", "subfigure",
    "multirow", "makecell", "longtable", "tabularx", "colortbl",
    "enumitem",
    "pifont", "wasysym",
    "url",
    # `cite` removed — clashes with natbib that llmxive.cls auto-loads.
    # See the NOTE block below for details (PROJ-567 AnyFlow failure).
    "ulem", "soul",
    "lipsum",
    "verbatim", "fancyvrb", "listings",
    "siunitx",
    "tikz", "pgfplots",
    "rotating",
    # NOTE: `cite` is INTENTIONALLY excluded. The llmxive class auto-loads
    # `natbib` at endinput (see papers/.style/llmxive.cls); `cite` clashes
    # with natbib, causing the body's `\cite{...}` to runaway-parse as
    # `\cite[NOTE]{...}`. Symptom: PROJ-567 (AnyFlow) compile-failed with
    # "Paragraph ended before \@citex was complete" on every cite.
    "tcolorbox",
    "cleveref",
    "float",                   # \begin{figure}[H]
    "placeins",                # \FloatBarrier
    "mathrsfs",                # \mathscr (script math)
    "adjustbox", "calc",
    "appendix",
    "xspace",
    "hyphenat", "parskip",
    # NOTE: `setspace` is intentionally NOT forwarded — the llmxive class
    # provides \singlespacing / \onehalfspacing / \doublespacing as no-op
    # stubs (`\providecommand` in llmxive.cls:197-209), and the class
    # owns the spacing decision. Loading setspace later collides with
    # `! LaTeX Error: Command \singlespacing already defined.` (PROJ-569
    # was the canary). If a future paper genuinely needs setspace, the
    # answer is to scope the spacing locally in the body, not to forward
    # the package.
    "etoolbox",
    "multicol",
    "changepage",
    "fontawesome", "fontawesome5",   # \faTimesCircle, \faGithub, etc.
    "bbm", "bbding", "dsfont",        # math blackboard fonts often used
    "graphicx",                       # llmxive provides it, but harmless
    "epsfig",                         # legacy graphics
    "wrapfig",                        # text-wrap around figures
    "amsthm",                         # theorem/proof envs
    "thmtools",
    "footmisc",                       # footnote variants
    "anyfontsize",                    # arbitrary font sizes in math
    "ifthen",
}

_USEPACKAGE_RE = re.compile(
    r"\\(?:usepackage|RequirePackage)\s*"
    r"(?:\[([^\]]*)\])?\s*"
    r"\{([^}]+)\}",
)


def _forwarded_packages(*sources: str) -> list[str]:
    """Return the deduped `\\usepackage[opts]{name}` lines we want to keep.

    Accepts one or more TeX strings — typically the original preamble PLUS
    the body of every bundled `.cls` file we can find. Bundled classes
    routinely `\\RequirePackage{natbib}` etc., so without scanning them
    the body's `\\citep` calls would die as undefined.

    Dedup is **by package name only** — first occurrence wins (preamble
    is scanned before bundled classes). LaTeX considers loading the same
    package twice with different option sets an `! Option clash` fatal
    error (PROJ-569 had `\\usepackage[numbers]{natbib}` followed by
    `\\usepackage[square, numbers]{natbib}` from a bundled cls; both
    options would pass the prior `(name, opts)` dedup as distinct keys).
    """
    out: list[str] = []
    seen: set[str] = set()
    for src in sources:
        for m in _USEPACKAGE_RE.finditer(src):
            opts, names = (m.group(1) or "").strip(), m.group(2)
            for name in (n.strip() for n in names.split(",")):
                if not name or name not in _SAFE_FORWARD_PACKAGES:
                    continue
                if name in seen:
                    continue
                seen.add(name)
                # natbib is ALWAYS loaded by llmxive.cls itself (with the
                # house options `numbers,compress,sort`). Forwarding it again
                # WITH options causes a fatal `! Option clash for package
                # natbib` whenever the paper's own options differ from the
                # class's (e.g. PROJ-603 used `[numbers, sort&compress]`,
                # which is a different option string than `numbers,compress,
                # sort` → clash → arXiv-fallback). Emit it WITHOUT options:
                # a bare re-request of an already-loaded package is a no-op,
                # and the class's options win — which is the intended house
                # citation style anyway.
                if name == "natbib":
                    out.append(r"\usepackage{natbib}")
                elif opts:
                    out.append(rf"\usepackage[{opts}]{{{name}}}")
                else:
                    out.append(rf"\usepackage{{{name}}}")
    return out


# algorithm2e is mutually INCOMPATIBLE with the algorithmicx family
# (algpseudocode) and the classic `algorithmic` package: they each define
# the `algorithmic` environment / `\State` / `\For` etc. differently.
# Loading both leaves the algorithmic list environment half-defined, so
# `\end{algorithmic}` fails to restore the text width and EVERY following
# paragraph renders in a ~1-inch column (PROJ-571: a 30-page paper blew up
# to 107 pages of one-word-per-line text). Venue .cls bundles sometimes
# `\RequirePackage` all of them, so the extractor forwards the whole
# conflicting set. Resolve by which family the BODY actually uses.
_ALG2E_USAGE_RE = re.compile(
    r"\\(?:KwIn|KwOut|KwData|KwResult|KwRet|SetKwInOut|SetKwFunction|"
    r"SetKwData|SetAlgoLined|SetAlgoNoLine|DontPrintSemicolon|BlankLine|"
    r"Indp|Indm|tcp|tcc|eIf|lIf|lElse|uIf|uElse|SetKw)\b"
    r"|\\begin\{algorithm2e\}"
)
_ALGX_USAGE_RE = re.compile(
    r"\\(?:State|Statex|EndFor|EndIf|EndWhile|EndProcedure|EndFunction|"
    r"EndLoop|Procedure|Ensure|Require)\b"
)


def _resolve_algorithm_conflict(pkgs: list[str], body: str) -> list[str]:
    """Drop the algorithm-package family the body does NOT use, so
    `algorithm2e` and `algpseudocode`/`algorithmic` never coexist."""
    have_a2e = any("algorithm2e" in p for p in pkgs)
    have_algx = any(("algpseudocode" in p) or ("algorithmicx" in p)
                    or ("algorithmic" in p and "algorithmicx" not in p)
                    for p in pkgs)
    if not (have_a2e and have_algx):
        return pkgs
    a2e_hits = len(_ALG2E_USAGE_RE.findall(body))
    algx_hits = len(_ALGX_USAGE_RE.findall(body))
    # Default to keeping the algorithmicx family (the class supports it and
    # most arXiv papers use \State/\For), drop algorithm2e — unless the body
    # clearly uses algorithm2e more.
    drop_a2e = a2e_hits <= algx_hits
    out: list[str] = []
    for p in pkgs:
        if drop_a2e and "algorithm2e" in p:
            continue
        if not drop_a2e and (("algpseudocode" in p) or
                             ("algorithmic" in p and "algorithmicx" not in p)):
            continue
        out.append(p)
    return out


# Layout / sizing / margin commands we explicitly DROP from preambles —
# these fight the llmxive class. The user's request: "things like 2 column
# view, geometry (custom margins/spacing/font sizing), etc. should all
# also be stripped out."
_LAYOUT_KILL_COMMANDS = {
    "twocolumn", "onecolumn",
    "pagestyle", "thispagestyle",
    "setlength", "addtolength",          # margin/spacing tweaks
    "geometry",                            # \geometry{...} (from geometry pkg)
    "renewcommand@baselinestretch",       # placeholder; handled below
}
# Commands whose body we drop entirely when found in preamble — these
# alter document layout in incompatible ways.
_LAYOUT_KILL_RE = re.compile(
    r"\\(?:twocolumn|onecolumn|geometry|pagestyle|thispagestyle"
    r"|columnsep|columnseprule|setpapersize|setlrmarginsandblock"
    r"|setulmarginsandblock|checkandfixthelayout|raggedbottom"
    r"|raggedright|raggedleft)\b"
    r"(?:\s*\[[^\]]*\])?"
    r"(?:\s*\{[^}]*\})*"
)

# `\setlength{\X}{Y}` and `\addtolength{...}` — drop only when the
# target is a layout-related length register. We never drop math-related
# length tweaks.
_LAYOUT_LENGTH_NAMES = {
    "textwidth", "textheight", "linewidth", "columnwidth",
    "oddsidemargin", "evensidemargin", "topmargin", "bottommargin",
    "headheight", "headsep", "footskip",
    "parindent", "parskip", "leftmargin", "rightmargin",
    "columnsep", "columnseprule",
    "abovecaptionskip", "belowcaptionskip",
    "baselineskip", "baselinestretch",
    "marginparwidth", "marginparsep", "marginparpush",
    "hsize", "vsize", "voffset", "hoffset",
}
_SETLENGTH_RE = re.compile(
    r"\\(?:set|add(?:to)?)length\s*\{\\([A-Za-z@]+)\}\s*\{[^}]*\}"
)

# Font-shape redirects we drop — they fight fontspec / our class.
_FONT_KILL_RE = re.compile(
    r"\\renewcommand\s*\{\\(?:rm|sf|tt|bf|md|sl|it|sc|up|en)default\}\s*\{[^}]*\}"
)
_FONT_SIZE_KILL_RE = re.compile(
    r"\\renewcommand\s*\{\\(?:normalsize|small|footnotesize|tiny|"
    r"large|Large|LARGE|huge|Huge)\}\s*\{[^}]*\}"
)


def _strip_layout_directives(tex: str) -> str:
    """Remove layout/margin/column/font-size directives from a TeX
    string. Applied to both the original preamble (before we discard it)
    and to the body (where leftover `\\twocolumn` or `\\setlength{...}`
    calls can still throw off the llmxive layout).
    """
    tex = _LAYOUT_KILL_RE.sub("", tex)
    tex = _FONT_KILL_RE.sub("", tex)
    tex = _FONT_SIZE_KILL_RE.sub("", tex)

    def _drop_layout_setlength(m: re.Match[str]) -> str:
        name = m.group(1)
        return "" if name in _LAYOUT_LENGTH_NAMES else m.group(0)
    tex = _SETLENGTH_RE.sub(_drop_layout_setlength, tex)
    return tex


# LaTeX kernel + ubiquitous standard-package commands; never forward
# user-defined re-versions of these from .cls files (would collide).
_LATEX_KERNEL_NAMES = {
    "documentclass", "usepackage", "RequirePackage", "ProvidesClass",
    "NeedsTeXFormat", "LoadClass", "PassOptionsToClass",
    "PassOptionsToPackage", "DeclareOption", "ProcessOptions",
    "ExecuteOptions", "AtBeginDocument", "AtEndDocument",
    "ClassError", "ClassWarning", "ClassInfo",
    "PackageError", "PackageWarning", "PackageInfo",
    "newcommand", "renewcommand", "providecommand", "def",
    "edef", "gdef", "xdef", "let", "global", "long",
    "newenvironment", "renewenvironment", "newcounter",
    "newif", "newdimen", "newskip", "newlength",
    "newbox", "newread", "newwrite", "newtoks",
    "newcount", "newmuskip", "newhelp", "newinsert",
    "newfont",
    "begin", "end", "title", "author", "date", "thanks",
    "maketitle", "tableofcontents", "listoffigures", "listoftables",
    "appendix", "section", "subsection", "subsubsection",
    "paragraph", "subparagraph", "chapter", "part",
    "footnote", "footnotemark", "footnotetext",
    "caption", "label", "ref", "pageref", "cite", "bibitem",
    "bibliography", "bibliographystyle",
    "input", "include", "includegraphics", "includepdf",
    "item", "items", "subitem",
    "frac", "sum", "prod", "int", "lim", "sup", "inf",
    "text", "mathrm", "mathbf", "mathit", "mathsf", "mathtt",
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta",
    "eta", "theta", "iota", "kappa", "lambda", "mu", "nu",
    "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta",
    "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu", "Nu",
    "Xi", "Pi", "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega",
    "and", "or", "in", "not", "neq", "leq", "geq", "approx",
    "to", "rightarrow", "leftarrow", "cdot", "times", "div",
    "par", "noindent", "indent", "vspace", "hspace", "smallskip",
    "medskip", "bigskip", "newpage", "clearpage", "pagebreak",
    "textbf", "textit", "textsf", "texttt", "textrm", "textsc",
    "emph", "underline", "url", "href", "hyperref",
    "color", "textcolor", "definecolor", "colorbox",
    "raisebox", "framebox", "fbox", "mbox", "parbox",
    "centerline", "centering", "raggedleft", "raggedright",
    "tiny", "scriptsize", "footnotesize", "small", "normalsize",
    "large", "Large", "LARGE", "huge", "Huge",
}


def seen_names_from_forwarded(forwarded: list[str]) -> set[str]:
    """Pull the macro names out of `\\providecommand{\\name}...` lines."""
    names = set()
    for line in forwarded:
        m = re.search(r"\\providecommand\s*\{\\([A-Za-z@]+)\}", line)
        if m:
            names.add(m.group(1))
    return names


_TCB_DEF_CMDS = ("newtcolorbox", "renewtcolorbox", "providetcolorbox",
                 "DeclareTColorBox", "NewTColorBox")


def _forwarded_tcolorbox(source: str) -> list[str]:
    """Forward tcolorbox configuration the body relies on: `\\tcbuselibrary`,
    `\\tcbset` styles, and `\\newtcolorbox` environment definitions.

    Venue `.cls`/`.sty` bundles define custom callout/prompt boxes
    (`\\newtcolorbox{promptbox}{...}`, `\\tcbset{agentscope/.style={...}}`)
    in the preamble — which we discard. Without the definition the body's
    `\\begin{promptbox}` / `\\begin{tcolorbox}[agentscope]` either errors or
    (shimmed) dumps its content unboxed, where long prompt text overflows the
    margin by hundreds of pt (PROJ-565, PROJ-601) or a styled callout loses
    its frame (PROJ-606). Forwarding the definitions restores proper, content-
    wrapping boxes. `\\tcbuselibrary` is forwarded first so `breakable`/`skins`
    are available to the definitions that need them.
    """
    src = _strip_tex_comments(source)
    libs: list[str] = []
    sets: list[str] = []
    defs: list[str] = []
    seen: set[str] = set()

    for m in re.finditer(r"\\tcbuselibrary\s*(?:\[[^\]]*\])?\s*\{[^}]*\}", src):
        if m.group(0) not in seen:
            seen.add(m.group(0)); libs.append(m.group(0))

    for m in re.finditer(r"\\tcbset\b", src):
        arg, _ = _capture_braced_arg(src, m.end())
        # Forward ONLY style DEFINITIONS (`name/.style={…}`) — these register
        # a reusable named style the body invokes via `[name]`. Bare option-
        # setting (`\tcbset{colback=…}`) is skipped: it's usually scoped
        # inside another macro (PROJ-601 set it inside \mymaketitle) and
        # forwarding it would restyle EVERY box globally with venue colours.
        if arg is not None and re.search(r"/\.(?:style|append\s*style|code|init)\b", arg):
            piece = "\\tcbset{" + arg + "}"
            if piece not in seen:
                seen.add(piece); sets.append(piece)

    for cmd in _TCB_DEF_CMDS:
        for m in re.finditer(r"\\" + cmd + r"\b", src):
            i = m.end()
            piece = "\\" + cmd
            bm = re.match(r"\s*\[[^\]]*\]", src[i:])      # optional [init]
            if bm:
                piece += src[i:i + bm.end()]; i += bm.end()
            name, i = _capture_braced_arg(src, i)          # {name}
            if name is None:
                continue
            piece += "{" + name + "}"
            for _ in range(2):                              # optional [n][default]
                bm = re.match(r"\s*\[[^\]]*\]", src[i:])
                if bm:
                    piece += src[i:i + bm.end()]; i += bm.end()
                else:
                    break
            body, i = _capture_braced_arg(src, i)           # {body}
            if body is None:
                continue
            piece += "{" + body + "}"
            if name.strip() not in seen:
                seen.add(name.strip()); defs.append(piece)

    return libs + sets + defs


def _forwarded_definecolor(source: str) -> list[str]:
    """Capture `\\definecolor{name}{model}{spec}` calls from anywhere in
    the source. These often live in bundled `.cls` files and the body
    references the names via `\\textcolor{name}{...}` or `\\color{name}`.
    """
    out: list[str] = []
    seen: set[str] = set()
    i = 0
    n = len(source)
    pat = re.compile(r"\\definecolor\s*")
    while i < n:
        m = pat.search(source, i)
        if not m:
            break
        # Parse: \definecolor{name}{model}{spec}
        idx = m.end()
        name, idx = _capture_braced_arg(source, idx)
        if name is None:
            i = m.end()
            continue
        model, idx = _capture_braced_arg(source, idx)
        if model is None:
            i = m.end()
            continue
        spec, idx = _capture_braced_arg(source, idx)
        if spec is None:
            i = m.end()
            continue
        if name not in seen:
            seen.add(name)
            out.append(rf"\definecolor{{{name}}}{{{model}}}{{{spec}}}")
        i = idx
    return out


def _forwarded_newcommands_filtered(source: str, *, keep: set[str]) -> list[str]:
    """Like `_forwarded_newcommands` but only emits definitions whose
    name is in `keep` — used for selective scanning of bundled .cls
    files (forward `\\mindlabasset` because the body uses it; skip
    `\\toclevel` because the body doesn't).
    """
    if not keep:
        return []
    all_cmds = _forwarded_newcommands(source)
    out: list[str] = []
    for line in all_cmds:
        m = re.search(r"\\providecommand\s*\{\\([A-Za-z@]+)\}", line)
        if m and m.group(1) in keep:
            out.append(line)
    return out


def _forwarded_newcommands(source: str) -> list[str]:
    """User-defined `\\newcommand` / `\\renewcommand` / `\\providecommand`
    / `\\def` directives from `source` (typically the FULLY-INLINED tex,
    so macros defined in `\\input`ed files also get picked up — per the
    user's note: "if any macros are defined directly in the document, or
    even in an included file, those can be programmatically replaced").
    Forwarded as `\\providecommand` so they don't clash with the class.
    """
    out: list[str] = []
    seen_names: set[str] = set()

    # 1) \newcommand{\foo}[N][default]{body}
    nc_re = re.compile(
        r"\\(?:newcommand|renewcommand|providecommand)\*?\s*"
        r"\{\\([A-Za-z@]+)\}"          # \name
        r"(?:\s*\[(\d+)\])?"          # optional [N]
        r"(?:\s*\[([^\]]*)\])?"       # optional [default]
    )
    # Walk matches with an exclusion list: any match whose START falls
    # inside a previously-captured body is a NESTED definition (e.g.
    # mindlab.cls's `\renewcommand{\title}[2]{\newcommand{\titlelist}{... #2 ...}}`
    # captures both \title and \titlelist; the inner is meaningless
    # without the outer scope and references its outer arity. Skip nested.
    captured_spans: list[tuple[int, int]] = []
    for m in nc_re.finditer(source):
        if any(s <= m.start() < e for s, e in captured_spans):
            continue
        name, arity, default = m.group(1), m.group(2), m.group(3)
        body, end = _capture_braced_arg(source, m.end())
        if body is None:
            continue
        captured_spans.append((m.start(), end))
        if name in seen_names or name in _KNOWN_SHIMS:
            continue
        # Strip comments from the captured body. A macro whose body (and
        # closing brace) lives entirely on `%`-comment lines — a *disabled*
        # definition — would otherwise re-emit with its closing brace
        # commented out, leaving `\providecommand{\foo}[1]{` unclosed and
        # crashing the compile with "File ended while scanning use of
        # \@argdef" (PROJ-603's bytedance macros.tex had
        # `\providecommand{\authorheading}[1]{%` … `% }`). Stripping
        # comments here matches what LaTeX does at definition time; if the
        # result is brace-unbalanced (close brace was commented), forward a
        # safe empty body instead of a broken one.
        body = _strip_tex_comments(body)
        _nb = re.sub(r"\\[{}]", "", body)
        if _nb.count("{") != _nb.count("}"):
            body = ""
        # Sanity: if the body references `#N` for an N larger than the
        # declared arity, this command can't stand alone in a clean
        # `\providecommand` — usually a sign of nested definitions or
        # `\@` internal machinery we can't safely hoist. Skip it.
        declared_arity = int(arity) if arity else 0
        max_param = max(
            (int(x) for x in re.findall(r"#(\d)", body)),
            default=0,
        )
        if max_param > declared_arity:
            continue
        seen_names.add(name)
        if arity is not None and default is not None:
            out.append(rf"\providecommand{{\{name}}}[{arity}][{default}]{{{body}}}")
        elif arity is not None:
            out.append(rf"\providecommand{{\{name}}}[{arity}]{{{body}}}")
        else:
            out.append(rf"\providecommand{{\{name}}}{{{body}}}")

    # 2) \def\foo<params>{body}   — TeX-primitive form. The parameter
    #    text between `\foo` and `{` is a *parameter pattern* (e.g.
    #    `#1#2`, `#1[#2]`, even literal text). For provideability we
    #    only forward the simple `#1...#N` runs; anything fancy gets
    #    skipped (the original would have needed a real TeX engine
    #    to honor the pattern faithfully).
    def_re = re.compile(r"\\def\s*\\([A-Za-z@]+)\s*([^{]*)\{")
    for m in def_re.finditer(source):
        name = m.group(1)
        params = m.group(2)
        if name in seen_names or name in _KNOWN_SHIMS:
            continue
        # rewind to the "{" — _capture_braced_arg expects to find one
        body, _ = _capture_braced_arg(source, m.end() - 1)
        if body is None:
            continue
        # Only accept simple consecutive `#1#2..#N` patterns. Anything
        # with literal text in the parameter pattern is too risky to
        # round-trip as a `\providecommand`.
        params = params.strip()
        if params and not re.fullmatch(r"(#\d)+", params):
            continue
        arity = 0
        if params:
            # max # number seen — usually equals the count
            nums = [int(x) for x in re.findall(r"#(\d)", params)]
            arity = max(nums) if nums else 0
        seen_names.add(name)
        if arity:
            out.append(rf"\providecommand{{\{name}}}[{arity}]{{{body}}}")
        else:
            out.append(rf"\providecommand{{\{name}}}{{{body}}}")

    return out


# ───────────────────────────────────────────────────────────────────────
# 7. Extract bibliography directives from body
# ───────────────────────────────────────────────────────────────────────

def _extract_bibliography(body: str) -> tuple[str | None, str | None]:
    """Return (`\\bibliography{...}`-line, `\\bibliographystyle{...}`-line)
    or (None, None). If a `.bbl` is already present alongside the source
    we could `\\input{}` it directly, but the recipe still needs
    bibliography commands so we capture them as-is.
    """
    bib_m = re.search(r"\\bibliography\s*\{([^}]+)\}", body)
    sty_m = re.search(r"\\bibliographystyle\s*\{([^}]+)\}", body)
    return (
        bib_m.group(0) if bib_m else None,
        sty_m.group(0) if sty_m else None,
    )


# ───────────────────────────────────────────────────────────────────────
# 8. Build the wrapper
# ───────────────────────────────────────────────────────────────────────

_WRAPPER_HEADER = r"""%% =====================================================================
%% main-llmxive.tex — content-extracted llmXive wrapper
%% =====================================================================
%% Generated by scripts/extract_paper_content.py. The original paper
%% body is preserved; the venue-specific preamble (class, bundled .cls
%% files, custom packages) is DISCARDED and replaced with the llmxive
%% house style + a shim block that no-ops any venue-specific macros the
%% body still references.
%% =====================================================================
\documentclass{llmxive}
"""


def _break_repeated_plus(s: str) -> str:
    """Insert `{}` between every consecutive pair of `+` characters so
    Fraunces's contextual layout doesn't fuse them into a double-plus
    glyph. Idempotent and safe on strings that don't contain `++`."""
    return re.sub(r"\+(?=\+)", "+{}", s)


def build_wrapper(
    *,
    title: str | None,
    author: str | None,
    arxiv_id: str,
    paper_status: str = "Preprint",
    forwarded_packages: list[str],
    forwarded_newcommands: list[str],
    body: str,
    abstract: str | None = None,
) -> str:
    """Assemble the final wrapper .tex."""
    parts: list[str] = [_WRAPPER_HEADER]

    if forwarded_packages:
        parts.append("\n%% ── Packages forwarded from original preamble ─────────────────")
        parts.extend(forwarded_packages)

    parts.append("\n%% ── Shim layer (venue macros made into no-ops) ────────────────")
    parts.append(_shim_block())

    if forwarded_newcommands:
        parts.append("\n%% ── User-defined macros forwarded from original preamble ─────")
        # Wrap in \makeatletter...\makeatother. Without it, ANY forwarded
        # \providecommand{\@xxx}{...} fails: the `@` is not a letter in
        # the document scope, so `{\@xxx}` parses as `{\@ xxx}` →
        # `\providecommand` sees `\@` as the cmd name and `xxx{body}`
        # becomes raw preamble text that gets typeset at \begin{document}.
        # Symptoms seen in the wild:
        #   - PROJ-578 ("MemLens"): `\@noticestring` → "oticestring"
        #     leaked above the title block.
        #   - PROJ-580 ("Causal Forcing++"): `\@onedot` (from CVPR
        #     `\onedot` macro) → "nedot." leaked above the title.
        # Even non-@ macros are safe inside the block — \makeatletter
        # only affects how `@` is tokenized, not letter macros.
        parts.append(r"\makeatletter")
        parts.extend(forwarded_newcommands)
        parts.append(r"\makeatother")

    parts.append("\n%% ── llmXive paper metadata ──────────────────────────────────")
    if title:
        # Break Fraunces contextual `++` substitution by inserting an
        # empty brace group between consecutive plus characters. PROJ-580
        # ("Causal Forcing++") rendered as a double-strikethrough glyph
        # otherwise. The `+{}+` form is invisible to text extraction
        # (pdftotext still yields "Causal Forcing++") but blocks the
        # font's pair-substitution from firing.
        safe_title = _break_repeated_plus(title.strip())
        parts.append(rf"\title{{{safe_title}}}")
    if author:
        parts.append(rf"\author{{{author.strip()}}}")
    parts.append(rf"\paperid{{arXiv:{arxiv_id}}}")
    parts.append(rf"\paperstatus{{{paper_status}}}")

    parts.append("\n\\begin{document}")
    parts.append("\\maketitle")
    # If we captured an abstract (either as an env or via \abstract{...}
    # in the preamble), inject it explicitly here so it always lands on
    # the title page regardless of where the original source placed it.
    if abstract:
        parts.append("\\begin{abstract}")
        parts.append(abstract.strip())
        parts.append("\\end{abstract}")
    parts.append(body.strip())
    parts.append("\\end{document}\n")
    return "\n".join(parts)


# ───────────────────────────────────────────────────────────────────────
# 8b. Title / author / body cleanup helpers
# ───────────────────────────────────────────────────────────────────────

# Leading "Chapter N: " (case-insensitive, optional period after N) is
# common on book-chapter submissions. The website's project listing
# strips it heuristically — the published PDF should match.
_CHAPTER_PREFIX_RE = re.compile(
    # "Chapter N: ", "Chapter N. ", "Chapter N — ", "Chapter N - "
    # — all with optional whitespace, period after N, and one of
    # the common separators (or just whitespace after a period).
    r"^\s*Chapter\s+\d+\s*(?:[.:—-]\s+|\.\s+)\s*", re.IGNORECASE,
)


def _strip_chapter_prefix(title: str | None) -> str | None:
    """Drop a leading 'Chapter N: ' prefix from a title, if present."""
    if not title:
        return title
    return _CHAPTER_PREFIX_RE.sub("", title, count=1)


def _metadata_field(source_dir: Path, key: str) -> Any:
    """Read `paper/metadata.json::<key>` (the clean values captured at
    intake from the arXiv API). `source_dir` is `.../paper/source`, so the
    metadata sits one level up. Returns None on any failure."""
    meta_path = source_dir.parent / "metadata.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    return meta.get(key) if isinstance(meta, dict) else None


# Markup in a `\title{...}` that signals the source baked layout/styling
# into the title — a styled subtitle line, decorative symbols, font-size
# switches, colors, embedded logos, etc. When any of these appear we prefer
# the clean `metadata.json::title` (captured from the arXiv API) so the
# llmXive title page shows just the paper title, not a transplanted
# subtitle/decoration block. Examples this catches:
#   - PROJ-606: `\textbf{Code as Agent Harness}\\ {\fontsize..\scshape
#     \color..$\lozenge$~Toward Executable…~$\lozenge$}` → subtitle leaked
#   - PROJ-580: `Causal Forcing\\{\small ◇ Scalable Few-Step…}` → subtitle
_TITLE_MARKUP_RE = re.compile(
    r"\\\\"                         # line break → multi-line/subtitle
    r"|\\vspace|\\hspace"
    r"|\\fontsize|\\selectfont|\\scshape|\\textsc\b"
    r"|\\color\b|\\textcolor\b"
    r"|\\thanks\b|\\footnote\b"
    r"|\\includegraphics|\\raisebox"
    r"|\$"                          # inline math (decorative $\lozenge$ etc.)
)


def _clean_title(title: str | None, source_dir: Path) -> str | None:
    """If the extracted `\\title{...}` carries layout/styling markup (a
    baked-in subtitle, decorative symbols, font switches), prefer the clean
    `metadata.json::title`. Falls back to the raw title when no clean
    metadata title is available."""
    if not title or not _TITLE_MARKUP_RE.search(title):
        return title
    meta_title = _metadata_field(source_dir, "title")
    if isinstance(meta_title, str) and meta_title.strip():
        return meta_title.strip()
    return title


def _build_icml_author_line(full_tex: str) -> str | None:
    """Build a clean "Name¹, Name²" string from ICML's
    `\\icmlauthor{Name}{aff_key}` + `\\icmlaffiliation{aff_key}{Aff text}`
    declarations. Returns None when no ICML author list is present.

    The wrapper preamble's `\\author{...}` field is rendered by the
    llmxive class; we don't want raw \\icmlauthor macros leaking through
    (they were rendering as "Tsz Ting Chung* for: tszpa Tsz Ting
    Chungicml@vatime ..." with our no-op shims).
    """
    stripped = _strip_tex_comments(full_tex)
    # Find every \icmlauthor{NAME}{KEY}
    authors: list[tuple[str, str]] = []
    seen: set[str] = set()
    for m in re.finditer(r"\\icmlauthor\b", stripped):
        name, after = _capture_braced_arg(stripped, m.end())
        if name is None or not name.strip():
            continue
        key, _ = _capture_braced_arg(stripped, after)
        # Multiple authors can share a key; (Name, key) pair de-duped
        sig = (name.strip(), (key or "").strip())
        if sig in seen:
            continue
        seen.add(sig)
        authors.append((name.strip(), (key or "").strip()))
    if not authors:
        return None
    # Find every \icmlaffiliation{KEY}{TEXT} so we can number affiliations.
    aff_text: dict[str, str] = {}
    for m in re.finditer(r"\\icmlaffiliation\b", stripped):
        key, after = _capture_braced_arg(stripped, m.end())
        if key is None:
            continue
        text, _ = _capture_braced_arg(stripped, after)
        if text:
            aff_text[key.strip()] = text.strip()
    # Number unique affiliation keys in the order authors reference them.
    aff_idx: dict[str, int] = {}
    for _, k in authors:
        if k and k not in aff_idx:
            aff_idx[k] = len(aff_idx) + 1
    # Compose the author line: "Name¹, Name² · ¹Aff1 · ²Aff2"
    sups = "¹²³⁴⁵⁶⁷⁸⁹⁰"
    def _sup(n: int) -> str:
        return "".join(sups[int(c)] for c in str(n))
    author_pieces = []
    for name, k in authors:
        suffix = _sup(aff_idx[k]) if k in aff_idx else ""
        author_pieces.append(f"{name}{suffix}")
    aff_lines = [f"{_sup(i)}{aff_text.get(k, k)}"
                 for k, i in aff_idx.items() if (aff_text.get(k) or k)]
    out = ", ".join(author_pieces)
    if aff_lines:
        out += " \\\\ \\small " + " · ".join(aff_lines)
    return out


# ───────────────────────────────────────────────────────────────────────
# 8c. Body cleanup passes
# ───────────────────────────────────────────────────────────────────────

def _body_cleanup_passes(body: str) -> str:
    """Run a sequence of cosmetic scrubs over the document body so the
    rendered llmXive PDF doesn't show venue/template-specific artifacts.

    1. Drop `\\keywords{...}` lines — not part of the llmxive style.
    2. Convert `\\begin{wrapfigure}[opts]{pos}{width}...\\end{wrapfigure}`
       to a plain `\\begin{figure}...\\end{figure}` — wrapfigure often
       overflows the body width and breaks the layout.
    3. Strip `\\textcolor{NAME}{TEXT}` calls down to plain `TEXT` so the
       paper renders monochrome (the llmxive style is intentionally
       restrained on color).
    4. Strip standalone `\\color{NAME}` directives (these would carry
       color past the immediate command and pollute downstream text).
    5. Drop `\\IEEEpubid{...}` / `\\IEEEoverridecommandlockouts` /
       `\\copyrightnotice{...}` — IEEE-specific layout commands.
    """
    # 0a. Convert markdown code fences (```lang … ```) to a themed, wrapping
    #     lstlisting BEFORE any text scrub, so raw code isn't mangled and no
    #     longer overflows hundreds of pt into the margin (PROJ-601).
    body = _convert_markdown_code_fences(body)
    # 0b. Strip venue page-overlay banners (\AddToShipoutPicture* etc.) — the
    #     llmxive class owns the header/footer (PROJ-603).
    body = _strip_shipout_overlays(body)

    # 1. Drop \keywords{...}
    body = re.sub(
        r"\\keywords\s*\{[^}]*\}",
        "", body, flags=re.S,
    )
    # And the icml variant.
    body = re.sub(r"\\icmlkeywords\s*\{[^}]*\}", "", body, flags=re.S)

    # 1b. Strip decorative icon/emoji marker macros everywhere (fontawesome
    #     \faGithub, \twemoji, \coloremoji, dingbats). They render as tofu
    #     under the house fonts. PROJ-581/597/606 used these for Project-Page/
    #     Code teaser links and corresponding-author markers.
    body = _strip_icons_and_emoji(body)

    # 1c. Drop a centered "Project Page · Code · Models" resource-link row
    #     anywhere in the body — it's the title/abstract teaser (PROJ-581),
    #     never real body content (the check requires \href/\url + almost no
    #     prose, so figure `center` blocks are safe).
    body = _strip_resource_envs(body)
    # 1d. Drop "resource link" metadata lines (Keywords:/Github:/Code:/
    #     Project Page:/bare \href|\url link lines) — but ONLY in the body's
    #     leading title/teaser zone, so real reference links deeper in the
    #     paper are never touched. These leak from the source's title block
    #     after we transplant the title/author/affiliation (PROJ-565, 601,
    #     604: a bare GitHub URL left sitting between the authors and the
    #     abstract; PROJ-573: icon-prefixed Project-Page/Code lines).
    body = _strip_resource_lines(body, only_leading_chars=2500)

    # 2. wrapfigure → figure. We need brace-balanced argument capture
    # because wrapfigure takes 2-3 brace args before its content.
    body = _convert_wrapfigure(body)

    # 3. \textcolor{X}{Y} → Y  (keep the text, drop the color)
    body = _strip_textcolor(body)

    # 4. \color{X} → (nothing) — bare color switches outside groups bleed.
    body = re.sub(r"\\color\s*\{[^}]*\}", "", body)
    body = re.sub(r"\\color\s*\[[^]]*\]\s*\{[^}]*\}", "", body)

    # 5. IEEE-specific
    body = re.sub(r"\\IEEEpubid\s*\{[^}]*\}", "", body)
    body = re.sub(r"\\IEEEoverridecommandlockouts\b", "", body)
    body = re.sub(r"\\copyrightnotice\s*\{[^}]*\}", "", body)

    # 6. Wrap inline math in section headings with \texorpdfstring so
    #    hyperref doesn't try to PDF-encode the math and fail with
    #    `Improper alphabetic constant` / `Token not allowed in PDF
    #    string (Unicode)` (PROJ-569 / InternAtlas had
    #    `\subsection{Cross-Modal Regularizer $\Omega_{\text{cross}}$}`
    #    which crashed lualatex during hyperref bookmark generation).
    body = _wrap_section_math(body)

    # 7. Drop manual page-break directives — let LaTeX flow text
    #    naturally. PROJ-569 had `\clearpage` immediately before
    #    `\bibliography{ref}`, leaving a near-empty page between the
    #    Conclusion and References. The user's rule: references start
    #    right after the text ends. The llmxive class doesn't need
    #    manual breaks anywhere; if a future paper wants a page break
    #    in a specific spot, it should be a layout decision the class
    #    handles, not a body directive.
    body = re.sub(r"\\clearpage\b", "", body)
    body = re.sub(r"\\newpage\b", "", body)
    body = re.sub(r"\\pagebreak(?:\s*\[[0-4]\])?\b", "", body)

    # 8. Move every table's \caption (and any immediately-following
    #    \label) from the top to the bottom of the table block, so all
    #    captions sit BELOW their content — matching the llmxive style
    #    convention used for figures.
    body = _move_table_captions_below(body)

    # 9. Relax restrictive float-placement specs (`[h]` / `[H]`) on
    #    `table`/`figure` to `[!htbp]` so LaTeX can defer a tall float
    #    to the next page instead of forcing it "here" and overflowing
    #    the page footer (e.g. p.79 of the MemLens prototype showed a
    #    caption running BELOW the page number because `[h]` left no
    #    space for the caption after the tabular body).
    body = _relax_float_placement(body)

    return body


def _move_table_captions_below(body: str) -> str:
    """For every `\\begin{table}…\\end{table}` block, move any `\\caption{…}`
    (and an immediately-following `\\label{…}`) from above the tabular
    content to BELOW it. Figure captions are conventionally below;
    table captions are conventionally above. The user prefers table
    captions below too (consistency with figures).

    Scope: only `table` and `table*` environments. We do NOT touch
    figures (already-below convention) or wraptable (the previous
    cleanup pass already converted those to `table` floats, so they're
    picked up here too).

    Robustness:
      - Brace-balanced capture of the caption argument (so a `}` inside
        the caption text doesn't truncate).
      - Skip if the table has NO `\\caption` (e.g. it's a placeholder).
      - Skip if the `\\caption` already appears AFTER the `\\centering`
        or after `\\hline`/`\\toprule`/`\\bottomrule` — heuristic that
        it's already at the bottom.
    """
    cap_re = re.compile(r"\\caption\s*\{", re.IGNORECASE)
    lab_re = re.compile(r"^\s*\\label\s*\{[^}]*\}", re.IGNORECASE)
    out: list[str] = []
    for env in ("table\\*?",):
        # We rebuild `body` per env; only `table` for now (figure already
        # below by convention). The list is here so adding more later
        # is a one-line change.
        pass
    pat = re.compile(r"\\begin\s*\{(table\*?)\}", re.IGNORECASE)
    end_re_cache: dict[str, re.Pattern] = {}
    i = 0
    n = len(body)
    while i < n:
        m = pat.search(body, i)
        if not m:
            out.append(body[i:])
            break
        # Skip table blocks whose `\begin{table}` line is itself inside a
        # LaTeX comment (`%` before the macro on the same line). PROJ-569
        # had an entire `\begin{table}...\end{table}` block commented out
        # line-by-line; without this guard the caption-mover would lift
        # the caption out of its `%`-prefixed siblings and emit it as
        # uncommented prose, breaking the next un-commented \caption{}.
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_prefix = body[line_start:m.start()]
        if "%" in line_prefix and not line_prefix.rstrip().endswith("\\"):
            out.append(body[i:m.end()])
            i = m.end()
            continue
        out.append(body[i:m.start()])
        env_name = m.group(1)
        end_re = end_re_cache.setdefault(
            env_name, re.compile(r"\\end\s*\{" + re.escape(env_name) + r"\}", re.IGNORECASE),
        )
        em = end_re.search(body, m.end())
        if not em:
            out.append(body[m.start():])
            break
        block_open = body[m.start():m.end()]
        # Skip optional [pos] arg directly after \begin{table}
        idx = m.end()
        bracket_m = re.match(r"\s*\[[^\]]*\]", body[idx:em.start()])
        opts = ""
        if bracket_m:
            opts = bracket_m.group(0)
            idx += bracket_m.end()
        inner = body[idx:em.start()]
        block_close = body[em.start():em.end()]
        i = em.end()

        # Find a \caption in the inner.
        cap_m = cap_re.search(inner)
        if not cap_m:
            out.append(block_open + opts + inner + block_close)
            continue
        # Brace-balanced capture of the caption body.
        cap_arg_start = cap_m.end()
        depth = 1
        j = cap_arg_start
        while j < len(inner) and depth > 0:
            c = inner[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            # malformed — leave block alone
            out.append(block_open + opts + inner + block_close)
            continue
        caption_full = inner[cap_m.start():j + 1]
        rest_after_cap = inner[j + 1:]
        # Capture an immediately-following \label{...} on the next line.
        label_full = ""
        lab_m = lab_re.match(rest_after_cap)
        if lab_m:
            label_full = lab_m.group(0).strip()
            rest_after_cap = rest_after_cap[lab_m.end():]
        # The pre-caption portion of inner (everything before \caption).
        pre_caption = inner[:cap_m.start()].rstrip()
        # Heuristic: skip if caption already appears AFTER the tabular
        # rules (some papers do put it correctly below; don't double-flip).
        tab_end_re = re.compile(r"\\(?:end\s*\{tabular\*?\}|bottomrule|hline)", re.IGNORECASE)
        if tab_end_re.search(pre_caption):
            # caption is already after the tabular rules — leave it.
            out.append(block_open + opts + inner + block_close)
            continue
        # Reassemble: pre-caption content (centering, tabular, etc.) on top;
        # caption + label + any trailing content at the bottom.
        new_inner = (
            pre_caption
            + "\n"
            + rest_after_cap.lstrip("\n")
            + ("\n" if rest_after_cap and not rest_after_cap.endswith("\n") else "")
            + caption_full
            + (("\n" + label_full) if label_full else "")
            + "\n"
        )
        out.append(block_open + opts + new_inner + block_close)
    return "".join(out)


def _wrap_section_math(body: str) -> str:
    """For every `\\section{...}`/`\\subsection{...}`/etc. containing `$...$`,
    wrap each inline math run with `\\texorpdfstring{$<math>$}{<math>}`
    so hyperref's PDF-string conversion uses the math source verbatim
    instead of trying to typeset it (which fails in unicode-math).
    """
    section_re = re.compile(
        r"(\\(?:section|subsection|subsubsection|paragraph|subparagraph)\*?)\s*\{",
    )
    out: list[str] = []
    i = 0
    while i < len(body):
        m = section_re.search(body, i)
        if not m:
            out.append(body[i:])
            break
        out.append(body[i:m.start()])
        macro = m.group(1)
        out.append(macro + "{")
        # Walk brace-balanced argument
        depth = 1
        j = m.end()
        title_start = j
        while j < len(body) and depth > 0:
            c = body[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        title = body[title_start:j]
        # Wrap inline math in the title — the FIRST arg of \texorpdfstring
        # keeps the math (typeset in the visible heading); the SECOND arg
        # must be a plain-text fallback used in the PDF bookmark string.
        # Strip TeX backslashes from the second arg so it's safe for
        # hyperref's PDF-string conversion (which couldn't handle
        # `\Omega_{\text{cross}}` as a literal token).
        def _wrap_math(m: re.Match) -> str:
            inner = m.group(1)
            # Plain-text fallback: drop backslashes (so \Omega → Omega),
            # drop braces, collapse whitespace.
            plain = re.sub(r"\\[a-zA-Z@]+\*?", "", inner)
            plain = re.sub(r"[{}]", "", plain)
            plain = re.sub(r"\s+", " ", plain).strip() or "..."
            return r"\texorpdfstring{$" + inner + r"$}{" + plain + r"}"
        wrapped = re.sub(r"\$([^$]+)\$", _wrap_math, title)
        out.append(wrapped)
        out.append("}")
        i = j + 1
    return "".join(out)


def _relax_float_placement(body: str) -> str:
    """Rewrite restrictive `[h]` / `[H]` placement specs on `table` and
    `figure` floats to the permissive `[!htbp]` so LaTeX can defer to a
    later page when the float doesn't fit (rather than overflowing the
    page footer with the caption — visible failure mode on tall tables
    placed near a page bottom).

    Leaves `[!h]`, `[!htbp]`, `[t]`, etc. alone. The `H` placement comes
    from the `float` package and pins the float strictly in place; we
    can relax that to `!htbp` since arXiv-intake papers don't usually
    need strict-here positioning, and when they do they should use the
    `float` package explicitly with comments.
    """
    pat = re.compile(
        r"\\begin\{(table|figure)\}\s*\[(h|H)\]"
    )
    return pat.sub(r"\\begin{\1}[!htbp]", body)


def _convert_wrapfigure(body: str) -> str:
    """Replace every `\\begin{wrap{figure,table}}[N]{R}{W} ... \\end{wrap…}`
    with the full-width equivalent — preserving the inner content.

    The `wrapfig` package floats a figure/table inline with text wrapping
    around it. With our llmxive class's wider single-column body, those
    floats routinely overflow the textwidth and break paragraph flow on
    the page after (PROJ-569's bottom-of-page-12 wraptable corrupted the
    top of page 13). Converting to full-width `figure`/`table` floats
    lets LaTeX place them on their own page break, restoring clean text
    flow.

    Conversion mapping:
      \\begin{wrapfigure}[N]{R}{W} … \\end{wrapfigure}
        → \\begin{figure}[t]        … \\end{figure}
      \\begin{wraptable}[N]{R}{W}  … \\end{wraptable}
        → \\begin{table}[t]         … \\end{table}
    """
    for env_src, env_dst in (("wrapfigure", "figure"), ("wraptable", "table")):
        body = _convert_wrapped_env(body, env_src, env_dst)
    return body


def _convert_wrapped_env(body: str, env_src: str, env_dst: str) -> str:
    """Replace each `\\begin{env_src}[N]{R}{W} … \\end{env_src}` with
    `\\begin{env_dst}[t] … \\end{env_dst}` (full-width float).

    Inside the wrapfigure the source's `\\includegraphics[width=\\linewidth]`
    means `\\linewidth` is the WRAP container's width (e.g. `0.3\\linewidth`
    of the page). Once we convert to a plain `figure`, `\\linewidth` means
    the full text width, and the figure renders 3× too large — visible
    overflow into footers on the published PDF. So we capture the wrap
    width arg (the third `{W}` brace) and rewrite every inner
    `\\includegraphics[width=\\linewidth]` / `\\includegraphics[width=\\columnwidth]`
    to `\\includegraphics[width=W\\linewidth]` so the rendered size matches
    the original wrapfigure container.
    """
    out: list[str] = []
    pat = re.compile(r"\\begin\s*\{" + env_src + r"\}")
    end_pat = re.compile(r"\\end\s*\{" + env_src + r"\}")
    i = 0
    n = len(body)
    while i < n:
        m = pat.search(body, i)
        if not m:
            out.append(body[i:])
            break
        out.append(body[i : m.start()])
        idx = m.end()
        wrap_width_arg: str | None = None
        required_args_seen = 0
        # Skip up to 3 args. Each can be optional [...] or required {...}.
        for _ in range(3):
            while idx < n and body[idx] in " \t\r\n":
                idx += 1
            if idx >= n:
                break
            if body[idx] == "[":
                close = body.find("]", idx)
                if close < 0:
                    break
                idx = close + 1
            elif body[idx] == "{":
                arg, new_idx = _capture_braced_arg(body, idx)
                if new_idx is None:
                    idx = m.end()
                    break
                required_args_seen += 1
                # The wrap width is the SECOND required arg for
                # wrap{figure,table}: `\begin{wrapfigure}[N]{R}{W}`. The
                # first required arg is the row-position spec (l/r/i/o);
                # the second is the container width (e.g. `0.3\linewidth`).
                if required_args_seen == 2:
                    wrap_width_arg = arg
                idx = new_idx
            else:
                break
        em = end_pat.search(body, idx)
        if not em:
            out.append(body[m.start():])
            break
        inner = body[idx : em.start()]
        if wrap_width_arg:
            inner = _scale_inner_includegraphics(inner, wrap_width_arg)
        out.append(rf"\begin{{{env_dst}}}[t]" + "\n" + inner + "\n" + rf"\end{{{env_dst}}}")
        i = em.end()
    return "".join(out)


def _scale_inner_includegraphics(inner: str, wrap_width: str) -> str:
    """Inside a converted wrapfigure body, rewrite each
    `\\includegraphics[width=\\linewidth]` to `\\includegraphics[width=W]`
    where W is the original wrapfigure container width. Falls back to
    leaving the directive alone if the width spec is unparseable."""
    # Strip leading numeric coefficient if present: `0.3\linewidth` →
    # match exactly. We only fire when the inner uses one of the relative
    # width macros that referred to the WRAP container's width.
    width_unit_re = re.compile(
        r"(?<!\d)(?<!\.)\\(linewidth|columnwidth|hsize)\b"
    )
    inc_re = re.compile(
        r"(\\includegraphics\s*\[[^\]]*?width\s*=\s*)([^,\]]+?)(\s*[,\]])"
    )

    def repl(m: re.Match) -> str:
        prefix, val, suffix = m.group(1), m.group(2).strip(), m.group(3)
        # Only rewrite if val is a relative-to-container reference.
        if width_unit_re.search(val):
            # Multiply: e.g. `0.3\linewidth` * `\linewidth` = `0.3\linewidth`.
            # Pragmatically: replace `\linewidth` with the wrap_width arg.
            # NB: `wrap_width` is a literal TeX string like `0.3\linewidth`
            # or `\columnwidth`. It MUST be passed as a function replacement,
            # not a template string — `re.sub` interprets backslash escapes
            # (`\l`, `\c`, …) in a template and raises `re.error: bad escape`,
            # which previously crashed the WHOLE conversion (every paper with
            # a `\linewidth`/`\columnwidth` wrapfigure width: PROJ-579, 598,
            # 605 all fell back to the raw arXiv PDF because of this).
            new_val = width_unit_re.sub(lambda _m: wrap_width, val)
            return f"{prefix}{new_val}{suffix}"
        return m.group(0)

    return inc_re.sub(repl, inner)


def _strip_textcolor(body: str) -> str:
    """Replace `\\textcolor{COLOR}{TEXT}` with just `TEXT`, preserving
    brace-balanced content (color values are simple but content can
    contain nested braces and math).
    """
    out: list[str] = []
    i = 0
    n = len(body)
    while i < n:
        if body[i] == "\\" and body.startswith("\\textcolor", i):
            # Skip \textcolor + optional [model]
            idx = i + len("\\textcolor")
            while idx < n and body[idx] in " \t\r\n":
                idx += 1
            if idx < n and body[idx] == "[":
                close = body.find("]", idx)
                if close < 0:
                    out.append(body[i])
                    i += 1
                    continue
                idx = close + 1
            # color name
            color, idx = _capture_braced_arg(body, idx)
            if color is None:
                out.append(body[i])
                i += 1
                continue
            # text
            text, idx = _capture_braced_arg(body, idx)
            if text is None:
                # no second arg — eat the \textcolor + first arg
                i = idx
                continue
            out.append(text)
            i = idx
            continue
        out.append(body[i])
        i += 1
    return "".join(out)


# Icon / emoji macros that arXiv papers use as decorative affiliation
# markers, corresponding-author symbols, or section bullets. Under the
# llmxive class (fontspec + Fraunces/JetBrains Mono) these render as tofu
# boxes or wrong glyphs (the fontawesome/twemoji glyph fonts aren't part
# of the house style), so we strip them entirely. Each is a low-fidelity
# scrub: drop the marker, keep surrounding text. Examples in the wild:
#   - PROJ-606: `\coloremojicode{2709}` (✉ corresponding author),
#     `\faGithub`, `\textcolor{Maroon}{\faBullseye}` keyword bullet.
#   - PROJ-581/597: `\faGithub`/`\faCode` Project-Page/Code teaser links.
_ICON_EMOJI_RE = re.compile(
    r"\\fa[A-Za-z]+(?:\[[^\]]*\])?"          # fontawesome: \faGithub, \faBullseye[…]
    r"|\\twemoji(?:\[[^\]]*\])?\s*\{[^}]*\}"  # \twemoji[..]{..}
    r"|\\coloremoji(?:code)?\s*\{[^}]*\}"     # \coloremoji{..} / \coloremojicode{..}
    r"|\\emoji\s*\{[^}]*\}"                   # \emoji{..}
    r"|\\ding\s*\{[^}]*\}"                    # \ding{..} (pifont dingbats as markers)
)


def _strip_icons_and_emoji(text: str) -> str:
    """Remove decorative icon/emoji marker macros (fontawesome, twemoji,
    coloremoji, dingbats). They render as tofu under the house fonts."""
    return _ICON_EMOJI_RE.sub("", text)


# A "resource link" metadata line: authors append a `Keywords:` / `Github:`
# / `Code:` / `Project Page:` line (often icon-prefixed) right after the
# abstract or under the title block. These aren't part of the llmxive style
# — the website surfaces artifact links in the project modal — so we drop
# them from the abstract and from the body's leading teaser zone.
_RESOURCE_LABEL_RE = re.compile(
    r"^\s*"
    r"(?:Key\s*-?\s*words?|Index\s+Terms|Github|GitHub|Code|Codebase|"
    r"Project(?:\s*Page)?|Homepage|Home\s*Page|Website|Web\s*Page|"
    r"Data(?:set)?|Models?|Demo|Repository|Repo|Correspondence)\s*:",
    re.IGNORECASE,
)
# Spacing / layout commands that precede a resource label (`\vspace{5mm}`
# before `\textbf{Keywords}:`). Stripped from visible text so the anchored
# label match still fires.
_LAYOUT_PREFIX_RE = re.compile(
    r"\\(?:vspace|hspace|noindent|par|centering|raggedright|raggedleft"
    r"|smallskip|medskip|bigskip|smash|leavevmode|newline|break)\b"
    r"\s*(?:\*?\s*\{[^}]*\}|\*)?",
)
# A near-bare link line: dominated by \href/\url with little prose around it.
_LINK_ONLY_RE = re.compile(r"\\(?:href|url)\s*\{")


# Structural commands that must NEVER be dropped, even if they share a
# segment with a resource label. Swallowing one of these (e.g. an adjacent
# `\end{abstract}`) leaves the document malformed.
_STRUCTURAL_RE = re.compile(
    r"\\(?:begin|end|section|subsection|subsubsection|paragraph|chapter"
    r"|maketitle|input|include|item|caption|bibliography|appendix)\b"
)


def _resource_visible_text(segment: str) -> str:
    """Reduce a segment to its bare visible text: drop icons/emoji, unwrap
    `\\textcolor{c}{t}`→t and `\\textbf{t}`/`\\textit{t}`/… → t, drop `~`."""
    s = _strip_icons_and_emoji(segment)
    s = _strip_textcolor(s)
    for _ in range(3):
        s = re.sub(
            r"\\(?:textbf|textit|textsc|texttt|emph|mathbf|mathrm|large|Large|"
            r"normalsize|small|bfseries|itshape|scshape)\s*\{([^{}]*)\}",
            r"\1", s,
        )
    s = _LAYOUT_PREFIX_RE.sub(" ", s)
    return s.replace("~", " ").strip()


def _is_resource_line(segment: str) -> bool:
    """True when a `\\\\`/blank-line-delimited segment is a resource-metadata
    line (a `Keywords:`/`Code:`/… label, or a near-bare \\href/\\url link)
    rather than real prose. Never matches a segment carrying structural
    commands (so we can't strand an `\\end{abstract}` etc.)."""
    if _STRUCTURAL_RE.search(segment):
        return False
    s = _resource_visible_text(segment)
    if not s:
        return False
    if _RESOURCE_LABEL_RE.search(s):
        return True
    # Near-bare link line: contains \href/\url and, once URLs, commands and
    # markup are stripped, leaves almost no prose — just a short label like
    # "Project Page" / "Code". Computed aggressively so custom icon macros
    # (\projectpage, \github) and nested-brace labels
    # (\href{url}{{\text{Project Page}}}) are handled (PROJ-581).
    if _LINK_ONLY_RE.search(segment):
        prose = re.sub(r"https?://\S+|www\.\S+", " ", s)   # URLs
        prose = re.sub(r"\\[A-Za-z@]+", " ", prose)          # all commands
        prose = re.sub(r"[\\{}\[\]$&~|]", " ", prose)         # markup chars
        prose = re.sub(r"\s+", " ", prose).strip()
        return len(prose) <= 30
    return False


_RESOURCE_ENV_RE = re.compile(
    r"\\begin\s*\{(center|flushleft|flushright)\}(.*?)\\end\s*\{\1\}",
    re.S,
)


def _strip_resource_envs(text: str) -> str:
    """Remove a `center`/`flushleft`/`flushright` block whose content is just
    a row of resource links — the "Project Page · Code · Models" teaser many
    papers center right under the title/abstract (PROJ-581). Only fires when
    the block contains \\href/\\url and almost no prose, so figure/table
    `center` blocks (no links) and real centered prose are left alone."""
    def _repl(m: re.Match[str]) -> str:
        inner = m.group(2)
        if not re.search(r"\\(?:href|url)\b", inner):
            return m.group(0)
        prose = re.sub(r"https?://\S+|www\.\S+", " ", inner)
        prose = re.sub(r"\\[A-Za-z@]+", " ", prose)
        prose = re.sub(r"[\\{}\[\]$&~|]", " ", prose)
        prose = re.sub(r"\s+", " ", prose).strip()
        # A few short labels (Project Page / Code / Models / Demo) → drop.
        return "" if len(prose) <= 48 else m.group(0)
    return _RESOURCE_ENV_RE.sub(_repl, text)


def _strip_resource_lines(text: str, *, only_leading_chars: int | None = None) -> str:
    """Drop resource-metadata lines (Keywords:/Github:/Code:/Project Page:/
    bare link lines). Segments are delimited by LaTeX `\\\\` breaks and blank
    lines. When `only_leading_chars` is set, only the leading slice of the
    text is scrubbed (used for the body's title/teaser zone, so we never
    touch real link references deep in the paper)."""
    if only_leading_chars is not None and len(text) > only_leading_chars:
        head, tail = text[:only_leading_chars], text[only_leading_chars:]
    else:
        head, tail = text, ""
    # First remove centered resource-link rows (Project Page · Code · …).
    head = _strip_resource_envs(head)
    # Split on `\\` (one or more) and blank lines, keeping delimiters out.
    parts = re.split(r"(\\\\+|\n\s*\n)", head)
    kept: list[str] = []
    for i, part in enumerate(parts):
        # Odd indices are the delimiters captured by the split group.
        if i % 2 == 1:
            kept.append(part)
            continue
        if _is_resource_line(part):
            # Drop the segment AND the delimiter that preceded it so we don't
            # leave a dangling `\\`.
            if kept and re.fullmatch(r"\\\\+|\n\s*\n", kept[-1]):
                kept.pop()
            continue
        kept.append(part)
    return "".join(kept) + tail


# Shipout / page-overlay directives that venues use for submission banners,
# "Preprint" / arXiv stamps, copyright watermarks, and conference notices.
# They paint full-page-width content on every page (often via eso-pic),
# which (a) overflows the llmxive text block and (b) duplicates info the
# llmxive class already shows in its own header/footer (arXiv id, status,
# page number). We strip them — the house style owns page furniture.
# PROJ-603 carried a `\AddToShipoutPictureFG*{ … \makebox[\paperwidth] … }`
# banner that produced a 168pt overfull box on every page.
_SHIPOUT_CMD_RE = re.compile(
    r"\\(?:AddToShipoutPictureFG|AddToShipoutPictureBG|AddToShipoutPicture|"
    r"AtBeginShipoutNext|AtBeginShipout|AddEverypageHook|AddThispageHook|"
    r"backgroundsetup)\b\s*\*?\s*"
    r"(?:\[[^\]]*\])?\s*"
)


def _strip_shipout_overlays(body: str) -> str:
    """Remove `\\AddToShipoutPicture*`/`\\AtBeginShipout`/`backgroundsetup`
    page-overlay directives (and their brace-balanced argument)."""
    out: list[str] = []
    i, n = 0, len(body)
    while i < n:
        m = _SHIPOUT_CMD_RE.match(body, i)
        if m:
            j = m.end()
            if j < n and body[j] == "{":
                _, j = _capture_braced_arg(body, j)
            i = j
            continue
        out.append(body[i])
        i += 1
    return "".join(out)


# Markdown fenced code blocks (```lang … ```) sometimes survive into arXiv
# sources (authors paste prompt/JSON examples). LaTeX renders the literal
# back-ticks plus an unwrapped, justified paragraph that runs hundreds of pt
# into the margin (PROJ-601's JSON examples overflowed by 1000+pt). Convert
# them to a `lstlisting`, which the class themes (llmx style) AND wraps
# (breaklines=true) — turning raw fences into proper, contained code blocks.
_MD_FENCE_RE = re.compile(
    r"^[ \t]*```[ \t]*[A-Za-z0-9_+\-]*[ \t]*\n(.*?)\n[ \t]*```[ \t]*$",
    re.M | re.S,
)


def _convert_markdown_code_fences(body: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        code = m.group(1).rstrip("\n")
        # lstlisting is verbatim; guard the (vanishingly rare) case where the
        # fenced content itself contains the end delimiter.
        if r"\end{lstlisting}" in code:
            return m.group(0)
        return "\\begin{lstlisting}\n" + code + "\n\\end{lstlisting}"
    return _MD_FENCE_RE.sub(_repl, body)


# ───────────────────────────────────────────────────────────────────────
# 9. Top-level entry point
# ───────────────────────────────────────────────────────────────────────

def extract(
    source_dir: Path,
    entry_tex: str,
    *,
    arxiv_id: str,
    paper_status: str = "Preprint",
) -> dict[str, Any]:
    """Build a fresh wrapper string from the source's content alone.

    Returns a dict: {ok, wrapper_text, title, author, abstract,
                     packages, errors}.
    """
    entry = source_dir / entry_tex
    if not entry.is_file():
        return {"ok": False, "error": f"entry not found: {entry}"}

    full_tex = _resolve_tex(source_dir, entry)
    preamble, body = _slice_document(full_tex)
    if not body:
        return {"ok": False, "error": "no \\begin{document} ... \\end{document} found"}

    # Title: try standard \title first, then venue-specific aliases. ICML
    # uses \icmltitle{}; NeurIPS / CVPR sometimes wrap in their own macro.
    title = (
        _extract_macro(full_tex, "title")
        or _extract_macro(full_tex, "icmltitle")
        or _extract_macro(full_tex, "TitleHeading")   # IEEE
        or _extract_macro(full_tex, "paperTitle")
    )
    # Strip leading "Chapter N: " (case-insensitive) from titles so the
    # PDF and the project listing match. Book-chapter submissions often
    # carry this prefix in the source but the website's listing strips
    # it heuristically — we should produce the same prefix-free form.
    title = _strip_chapter_prefix(title)
    # If the source baked a styled subtitle / decorations into \title{...},
    # prefer the clean metadata.json title (PROJ-580, PROJ-606).
    title = _clean_title(title, source_dir)

    # Author: PREFER the canonical `paper/metadata.json::authors` list
    # captured at intake from the arXiv API. It's a clean list of plain
    # names — free of the affiliation superscripts, footnote markers
    # (†/‡/∗), embedded institution logos, and \href markup that pollute a
    # transplanted LaTeX `\author{}` block. Mining the source's `\author`
    # leaked exactly that cruft onto the title page (PROJ-570:
    # "Hanzhong Guo1,2 Jie Wu2,†…", PROJ-572: "Keming Wu1,12,†CUBE …",
    # PROJ-573/606: embedded logos & links). The body is still preserved
    # verbatim — only the title-page author line uses the clean list.
    author: str | None = None
    meta_authors = _metadata_field(source_dir, "authors")
    if isinstance(meta_authors, list):
        cleaned = [
            str(a).strip() for a in meta_authors
            if isinstance(a, str) and a.strip() and "\\" not in a
        ]
        if cleaned:
            author = " \\and ".join(cleaned)

    # Fall back to parsing the source when metadata has no usable author
    # list (home-grown papers without an arXiv-intake metadata.json):
    # standard \author{} OR repeated authblk-style \author[K]{Name} (which
    # we collect and \\and-join), then ICML's \icmlauthor list.
    if author is None:
        all_authors = _extract_all_macros(full_tex, "author")
        if len(all_authors) > 1:
            author = " \\and ".join(all_authors)
        elif len(all_authors) == 1:
            author = all_authors[0]
        else:
            author = _build_icml_author_line(full_tex)

    # Abstract can be in the BODY (most papers) OR in the preamble if the
    # source `\input{}`s an abstract file BEFORE `\begin{document}` —
    # PROJ-567 (AnyFlow) does exactly that. PROJ-566 uses `\abstract{...}`
    # (macro form, not environment) entirely in the preamble. Either way
    # we capture from the full inlined source and inject explicitly into
    # the wrapper body.
    abstract = (
        _extract_env(full_tex, "abstract")
        or _extract_macro(full_tex, "abstract")
    )
    # Strip any `\keywords{...}` / `\icmlkeywords{...}` from the abstract —
    # keywords aren't part of the llmxive style, and they sometimes live
    # inside `\begin{abstract}...\end{abstract}` (e.g. PROJ-568).
    if abstract:
        abstract = re.sub(r"\\keywords\s*\{[^}]*\}", "", abstract, flags=re.S)
        abstract = re.sub(r"\\icmlkeywords\s*\{[^}]*\}", "", abstract, flags=re.S)
        # Strip decorative icon/emoji markers, then drop the "Keywords:" /
        # "Github:" / "Code:" metadata lines authors append to the abstract
        # (PROJ-606 ended its abstract with
        #   \textcolor{Maroon}{\faBullseye}~\textbf{Keywords}: … \\
        #   \faGithub~\textbf{Github}: \url{…}
        # both of which leaked onto the title page).
        abstract = _strip_icons_and_emoji(abstract)
        abstract = _strip_textcolor(abstract)
        abstract = _strip_resource_lines(abstract)
        # A leading "Abstract:" label is redundant — the class prints the
        # ABSTRACT heading itself (PROJ-606 had `\textbf{\large Abstract:}`).
        # Match either `\textbf{… Abstract …}` or a `{… Abstract …}` group
        # at the very start; `[^{}]` keeps it from eating nested braces.
        abstract = re.sub(
            r"^\s*(?:\\noindent\s*)?"
            r"(?:\\(?:textbf|textsc|textit|emph)\s*\{[^{}]*?Abstract[^{}]*?\}"
            r"|\{[^{}]*?Abstract[^{}]*?\})"
            r"\s*",
            "", abstract, count=1, flags=re.IGNORECASE,
        )
        abstract = abstract.strip()

    # Body cleanup: drop title/author/affiliation/etc. (transplanted to
    # wrapper), then strip layout-warping commands (twocolumn, geometry,
    # margin/spacing tweaks, font-shape redirects), then run
    # _body_cleanup_passes to scrub other rendering artifacts (keyword
    # lines, color tags, wrapfigure → figure, raw \citep when natbib
    # isn't available, etc.).
    body_clean = _strip_body_commands(body)
    body_clean = _strip_layout_directives(body_clean)
    # Remove the body's own \begin{abstract}...\end{abstract} BEFORE the
    # cosmetic cleanup passes run — we inject the captured (and cleaned)
    # abstract explicitly in build_wrapper. Removing it first means the
    # resource-line scrub in _body_cleanup_passes never has to navigate
    # around the abstract's structure. (A prior ordering swallowed the
    # abstract's `\end{abstract}` when it dropped an adjacent `Github:` link
    # line, leaving the environment unclosed → "! LaTeX Error: Not in outer
    # par mode" — PROJ-606.)
    body_clean = re.sub(
        r"\\begin\s*\{abstract\}.*?\\end\s*\{abstract\}",
        "", body_clean, flags=re.S,
    )
    body_clean = _body_cleanup_passes(body_clean)

    # Read every bundled .cls / .sty file alongside the source — those
    # venue classes routinely `\RequirePackage` natbib / cleveref / etc.
    # and define helper macros that the body uses. We mine them for the
    # SAME information we mine from preamble.tex.
    cls_sources: list[str] = []
    for ext in ("*.cls", "*.sty"):
        for cls in source_dir.glob(ext):
            try:
                cls_sources.append(cls.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue

    fwd_pkgs = _forwarded_packages(preamble, *cls_sources)
    # Never forward algorithm2e alongside algpseudocode/algorithmic — the
    # mismatch leaks a ~1-inch text column across the whole document
    # (PROJ-571). Keep whichever family the body actually uses.
    fwd_pkgs = _resolve_algorithm_conflict(fwd_pkgs, body)
    # Forward user macros from the WHOLE inlined source — preamble +
    # body + every \input{}ed file (per the user's request: "if any
    # macros are defined directly in the document, or even in an
    # included file, those can be programmatically replaced too").
    fwd_cmds = _forwarded_newcommands(full_tex)

    # Then SELECTIVELY scan bundled .cls files: forward any user-style
    # macros the BODY actually references but that aren't in the kernel
    # / LaTeX2e / forwarded-so-far set. Bundled classes define lots of
    # internal machinery (\toclevel, \switcht, …) that collide with
    # the kernel — by intersecting with body usage we keep only the
    # ones the body genuinely needs (e.g. \mindlabasset).
    if cls_sources:
        body_macros = set(re.findall(r"\\([A-Za-z@]+)", body))
        already = set(seen_names_from_forwarded(fwd_cmds)) | _KNOWN_SHIMS.keys()
        # Also blocklist venue-internal macros — these are already in
        # _BODY_DROP_COMMANDS (so they're removed from the body) AND
        # their original .sty definitions are too complex/tied-to-state
        # to forward cleanly. e.g. ICML's `\icmlauthor` does `\ificmlshowauthors
        # \mbox...` which depends on internal \ificmlshowauthors flag.
        venue_internal = set(_BODY_DROP_COMMANDS)
        cls_cmds = _forwarded_newcommands_filtered(
            "\n".join(cls_sources),
            keep=body_macros - already - _LATEX_KERNEL_NAMES - venue_internal,
        )
        fwd_cmds.extend(cls_cmds)

    # ALWAYS forward `\definecolor` directives from the FULLY-INLINED
    # source AND bundled .cls files — colors are referenced by name in
    # the body (e.g. \color{mindlabfg}), and xcolor errors hard if the
    # color isn't defined. We use the rest-of-the-line form because
    # \definecolor takes 3 brace-balanced args.
    fwd_colors = _forwarded_definecolor(full_tex + "\n".join(cls_sources))
    fwd_cmds.extend(fwd_colors)

    # Strip \textcolor / \color inside the forwarded macro bodies too —
    # otherwise the body's `\icono`, `\gain{...}` etc. emit color markup
    # at expansion time, which leaks past the llmxive style intent.
    fwd_cmds = [_strip_textcolor(re.sub(r"\\color\s*\{[^}]*\}", "", c)) for c in fwd_cmds]

    # Forward tcolorbox config (\tcbuselibrary, \tcbset, \newtcolorbox) so
    # custom callout/prompt boxes the body uses render properly instead of
    # dumping unboxed, overflowing content (PROJ-565/601 promptbox, PROJ-606
    # agentscope). Appended AFTER the \color scrub above so the boxes' colour
    # KEYS (colback=, colframe=) survive verbatim.
    fwd_cmds.extend(_forwarded_tcolorbox(full_tex + "\n".join(cls_sources)))

    wrapper = build_wrapper(
        title=title, author=author,
        arxiv_id=arxiv_id, paper_status=paper_status,
        forwarded_packages=fwd_pkgs,
        forwarded_newcommands=fwd_cmds,
        body=body_clean,
        abstract=abstract,
    )
    return {
        "ok": True,
        "wrapper_text": wrapper,
        "title": title,
        "author": author,
        "abstract": abstract,
        "packages": fwd_pkgs,
        "newcommands_count": len(fwd_cmds),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("source_dir", type=Path)
    ap.add_argument("entry_tex", help="name of the top-level .tex (relative to source_dir)")
    ap.add_argument("--arxiv-id", default="0000.00000")
    ap.add_argument("--paper-status", default="Preprint")
    ap.add_argument("--out", default="main-llmxive.tex")
    ap.add_argument("--print-result", action="store_true")
    args = ap.parse_args(argv)

    res = extract(args.source_dir, args.entry_tex,
                  arxiv_id=args.arxiv_id, paper_status=args.paper_status)
    if not res["ok"]:
        print(f"[extract] error: {res.get('error')}", file=sys.stderr)
        return 2

    out_path = args.source_dir / args.out
    out_path.write_text(res["wrapper_text"], encoding="utf-8")
    print(f"[extract] wrote {out_path}")
    print(f"[extract]   title={(res['title'] or '')[:70]!r}")
    print(f"[extract]   author={(res['author'] or '')[:70]!r}")
    print(f"[extract]   abstract: {'yes' if res['abstract'] else 'no'}")
    print(f"[extract]   forwarded packages: {len(res['packages'])}")
    print(f"[extract]   forwarded \\newcommands: {res['newcommands_count']}")
    if args.print_result:
        print("---")
        print(res["wrapper_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
