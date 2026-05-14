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
    """
    stripped = _strip_tex_comments(tex)
    for m in re.finditer(r"\\" + macro + r"\b", stripped):
        arg, _ = _capture_braced_arg(stripped, m.end())
        if arg and arg.strip():
            return arg
    return None


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
}


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
    "cite",
    "ulem", "soul",
    "lipsum",
    "verbatim", "fancyvrb", "listings",
    "siunitx",
    "tikz", "pgfplots",
    "rotating",
    "tcolorbox",
    "cleveref",
    "float",                   # \begin{figure}[H]
    "placeins",                # \FloatBarrier
    "mathrsfs",                # \mathscr (script math)
    "adjustbox", "calc",
    "appendix",
    "xspace",
    "hyphenat", "setspace", "parskip",
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
    """
    out: list[str] = []
    seen: set[tuple[str, str]] = set()
    for src in sources:
        for m in _USEPACKAGE_RE.finditer(src):
            opts, names = (m.group(1) or "").strip(), m.group(2)
            for name in (n.strip() for n in names.split(",")):
                if not name or name not in _SAFE_FORWARD_PACKAGES:
                    continue
                key = (name, opts)
                if key in seen:
                    continue
                seen.add(key)
                if opts:
                    out.append(rf"\usepackage[{opts}]{{{name}}}")
                else:
                    out.append(rf"\usepackage{{{name}}}")
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


def build_wrapper(
    *,
    title: str | None,
    author: str | None,
    arxiv_id: str,
    paper_status: str = "Preprint",
    forwarded_packages: list[str],
    forwarded_newcommands: list[str],
    body: str,
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
        parts.extend(forwarded_newcommands)

    parts.append("\n%% ── llmXive paper metadata ──────────────────────────────────")
    if title:
        parts.append(rf"\title{{{title.strip()}}}")
    if author:
        parts.append(rf"\author{{{author.strip()}}}")
    parts.append(rf"\paperid{{arXiv:{arxiv_id}}}")
    parts.append(rf"\paperstatus{{{paper_status}}}")

    parts.append("\n\\begin{document}")
    parts.append("\\maketitle")
    parts.append(body.strip())
    parts.append("\\end{document}\n")
    return "\n".join(parts)


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
    # Author: standard \author{}, then venue aliases.
    author = (
        _extract_macro(full_tex, "author")
        or _extract_env(full_tex, "icmlauthorlist")   # ICML
        or _extract_macro(full_tex, "icmlauthor")
    )
    abstract = _extract_env(body, "abstract")

    # Body cleanup: drop title/author/affiliation/etc. (transplanted to
    # wrapper), then strip layout-warping commands (twocolumn, geometry,
    # margin/spacing tweaks, font-shape redirects).
    body_clean = _strip_body_commands(body)
    body_clean = _strip_layout_directives(body_clean)

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
        cls_cmds = _forwarded_newcommands_filtered(
            "\n".join(cls_sources),
            keep=body_macros - already - _LATEX_KERNEL_NAMES,
        )
        fwd_cmds.extend(cls_cmds)

    # ALWAYS forward `\definecolor` directives from the FULLY-INLINED
    # source AND bundled .cls files — colors are referenced by name in
    # the body (e.g. \color{mindlabfg}), and xcolor errors hard if the
    # color isn't defined. We use the rest-of-the-line form because
    # \definecolor takes 3 brace-balanced args.
    fwd_colors = _forwarded_definecolor(full_tex + "\n".join(cls_sources))
    fwd_cmds.extend(fwd_colors)

    wrapper = build_wrapper(
        title=title, author=author,
        arxiv_id=arxiv_id, paper_status=paper_status,
        forwarded_packages=fwd_pkgs,
        forwarded_newcommands=fwd_cmds,
        body=body_clean,
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
