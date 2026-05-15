#!/usr/bin/env python3
"""Restyle an arXiv paper's LaTeX source into the llmXive house style.

Spec 009 relationship (T060):
    The new deterministic pipeline at
    ``src/llmxive/pipeline/pdf_pipeline/`` provides a stricter restyle path
    (cite-order [N] refs, bounded figure widths, canonical \\authorblock,
    LLM-free guarantee with AST-static guard). Use it FIRST for new papers:

        python -m llmxive.pipeline.pdf_pipeline.cli build --source main.tex

    This legacy script remains the canonical implementation for:
      - figure-PDF ghostscript sanitization (Adobe Illustrator clipping)
      - editorial-summary + artifact-link rendering on the title page
      - arXiv-id metadata extraction
      - the canonical _CLASS_PROVIDED_PACKAGES / _FONT_PACKAGES /
        _LAYOUT_PACKAGES lists (imported BY the new pipeline at runtime —
        see restyle.py:_legacy_path).

    Keep both. The new pipeline is the deterministic-build entry point;
    this legacy script is the publication-flow entry point. They share
    constants via importlib (single source of truth, Constitution I).

Per the requirement: the paper content MUST be preserved EXACTLY — figures,
writing, tables, titles, authors, affiliations, web links, bibliography.
The ONLY thing that changes is the style (the document class). The body
between `\\begin{document}` and `\\end{document}` is copied byte-for-byte
into the wrapper; only the preamble is rewritten.

Inputs:
  source_dir: a directory containing the original `main.tex` (or another
              named entry-point .tex) and all its figures, .bbl, .bib, etc.
  out_tex:    the wrapper .tex to write (typically alongside the original,
              named `<base>-llmxive.tex` so the original is preserved).
  arxiv_id:   the arXiv id (e.g. "2510.21958") — embedded in the new
              preamble's metadata.
  paper_status: "Preprint" | "Peer Reviewed" | … — defaults to "Preprint".

Outputs:
  Writes the wrapper .tex. Returns a dict describing the conversion:
  what packages were stripped, what metadata was extracted, etc. (Useful
  for downstream automation / diagnostics.)

Usage:
  python scripts/restyle_arxiv_paper.py \\
    projects/PROJ-562-…/paper/source main-llmxive.tex 2510.21958

Compile the result from the repo root so the class's fontspec Path resolves:
  cd /path/to/llmXive
  TEXINPUTS=./papers/.style: xelatex -output-directory=projects/.../paper/pdf \\
    projects/.../paper/source/main-llmxive.tex
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Packages whose functionality the class already provides; the wrapper strips
# `\usepackage[...]{<pkg>}` lines for these (per the class README). Conflict
# usually manifests as "Option clash" or duplicate-redefinition errors.
_CLASS_PROVIDED_PACKAGES = {
    "geometry", "hyperref", "caption", "titlesec", "fancyhdr", "xcolor",
    "microtype", "graphicx", "booktabs", "array", "tabularx", "colortbl",
    "amsmath", "amssymb", "amsthm", "mathtools", "enumitem", "listings",
    "fontenc", "inputenc", "url", "ragged2e", "etoolbox", "xparse",
    "calc", "tikz", "lastpage",
    # NB: we deliberately do NOT strip `natbib` or `biblatex` — many arXiv
    # papers use them for \citep/\citet, and the class doesn't load them.
}
# Font-y packages that conflict with the class's fontspec setup. Stripping
# them is what lets the original keep its body but get the new typography.
_FONT_PACKAGES = {
    "pxfonts", "txfonts", "mathptmx", "newtxtext", "newtxmath", "times",
    "mathpazo", "palatino", "helvet", "arev", "courier", "libertinus",
    "libertine", "inconsolata", "fontspec",  # we re-add fontspec ourselves
}
# Spacing/layout packages that fight the class's geometry + linespread.
_LAYOUT_PACKAGES = {
    "setspace",   # original may have \doublespacing — we want single
    "lineno",     # line numbers — drop unless requested
    "authblk",    # \author overload — we use \author + \affiliation
}

# Regex for `\usepackage[opts]{name1,name2}` (handles multi-name and options).
_USEPKG_RE = re.compile(
    r"\\usepackage\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}",
    re.MULTILINE,
)
_DOCCLASS_RE = re.compile(r"\\documentclass\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
_BEGIN_DOC_RE = re.compile(r"\\begin\{document\}")
_END_DOC_RE = re.compile(r"\\end\{document\}")

_TITLE_RE = re.compile(r"\\title\s*\{(.+?)\}\s*(?:\n|$)", re.DOTALL)
# Author handling: papers come in two shapes —
#   (a) single `\author{All Authors With \and Separators}` (classic LaTeX)
#   (b) repeated `\author[1,2]{One Name}` lines (the `authblk` style, used
#       by PROJ-575 and many recent arXiv papers).
# We capture BOTH with a single regex that allows an optional `[...]`
# affiliation-key arg before the `{name}` block, and use re.findall to
# collect every match (re.search returned only the first, which dropped
# all authors except the first in the authblk shape).
_AUTHOR_RE = re.compile(
    r"\\author\s*(?:\[[^\]]*\])?\s*\{(.+?)\}\s*(?:\n|$)", re.DOTALL,
)
_DATE_RE = re.compile(r"\\date\s*\{(.+?)\}\s*(?:\n|$)", re.DOTALL)

# A custom \maketitle redefinition — strip from the preamble (the class
# defines its own). Match `\renewcommand{\maketitle}{...}` or
# `\renewcommand\maketitle{...}` greedy-until-balanced (approximated by
# the first `}\n`/`}\s*$` pair that closes the outer brace).
_MAKETITLE_REDEF_RE = re.compile(
    r"\\renewcommand\s*\*?\s*\{?\\maketitle\}?\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*",
    re.DOTALL,
)


# ────────────────────────────────────────────────────────────────────────────
# Figure-PDF sanitization (Adobe Illustrator export workaround)
# ────────────────────────────────────────────────────────────────────────────
#
# Many arXiv submissions embed PDFs exported from Adobe Illustrator that
# contain content-stream operators or bounding boxes outside the PDF spec.
# `pdflatex` is forgiving here because it just embeds the raw stream;
# `lualatex` is stricter and ends up *clipping* the rendered figure to the
# operators it could parse — usually showing only the top fragment.
#
# Workaround: re-emit each figure-PDF through ghostscript before the LaTeX
# compile. gs normalizes content streams + bounding boxes losslessly. We
# write sanitized copies in-place but keep `.orig.pdf` backups so the
# operation is reversible.
#
# Sanitized output goes into a sibling CACHE DIR (`figs/.sanitized/`) that
# mirrors the original `figs/` tree. The original PDFs in `figs/` are left
# untouched, so the canonical source-of-truth is whatever the paper authors
# committed. The lualatex compile then sets TEXINPUTS so the cache shadows
# `figs/`, picking up the sanitized variants automatically. This keeps git
# diffs clean and makes the script safe to re-run.

# Where sanitized copies live, relative to a paper's `source/` dir.
# Layout: `figs-sanitized/figs/foo.pdf` mirrors `figs/foo.pdf`. The wrapper
# sets `\graphicspath{{figs-sanitized/}{./}}` so any
# `\includegraphics{figs/foo.pdf}` resolves to the cached copy first; the
# original under `figs/` is the fallback. Dot-prefixed names like
# `.fig-cache/` are skipped by some graphicx versions, so we use a normal
# directory name and just gitignore it.
_SANITIZED_CACHE_SUBDIR = "figs-sanitized"


def _sanitize_figure_pdf(src_pdf: Path, dest_pdf: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Run `gs -sDEVICE=pdfwrite` from `src_pdf` to `dest_pdf`. Skips work if
    `dest_pdf` is already newer than `src_pdf` (mtime-based incremental).
    Returns `{ok, status, before_bytes, after_bytes, error}` where `status` is
    one of "wrote" / "cached" / "skipped" / "error".
    """
    if not src_pdf.is_file():
        return {"ok": False, "status": "error", "error": f"not a file: {src_pdf}"}
    if not shutil.which("gs"):
        return {"ok": False, "status": "error", "error": "ghostscript (gs) not on PATH"}
    # Incremental: skip if cached version is up-to-date.
    if dest_pdf.exists() and dest_pdf.stat().st_mtime >= src_pdf.stat().st_mtime:
        return {"ok": True, "status": "cached", "src": str(src_pdf), "dest": str(dest_pdf)}
    if dry_run:
        return {"ok": True, "status": "would-sanitize", "src": str(src_pdf), "dest": str(dest_pdf)}
    dest_pdf.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_pdf.with_suffix(".tmp.pdf")
    try:
        subprocess.run(
            [
                "gs", "-dNOPAUSE", "-dBATCH", "-dQUIET",
                "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
                "-dPDFSETTINGS=/prepress",  # preserve quality; lossless for vector
                f"-sOutputFile={tmp}", str(src_pdf),
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        if tmp.exists():
            tmp.unlink()
        return {"ok": False, "status": "error", "error": f"gs failed: {exc.stderr or exc}"}
    tmp.replace(dest_pdf)
    return {
        "ok": True, "status": "wrote",
        "before_bytes": src_pdf.stat().st_size,
        "after_bytes": dest_pdf.stat().st_size,
        "src": str(src_pdf), "dest": str(dest_pdf),
    }


def sanitize_figure_pdfs(source_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Walk `<source_dir>/figs/` and re-emit each PDF through ghostscript into
    the parallel cache `<source_dir>/figs/.sanitized/<same-relative-path>`.

    The original PDFs under `figs/` are NEVER modified. To use the cache,
    lualatex must be invoked with TEXINPUTS prefixed so `figs/.sanitized` is
    searched before `figs/`. The helper `texinputs_prefix(source_dir)` returns
    the right prefix.

    Returns a dict `{ok, cache_dir, wrote: [...], cached: [...], failed: [...]}`.
    """
    figs = source_dir / "figs"
    cache = source_dir / _SANITIZED_CACHE_SUBDIR
    if not figs.is_dir():
        return {"ok": True, "cache_dir": str(cache), "wrote": [], "cached": [], "failed": [],
                "note": f"no figs/ dir under {source_dir}"}
    wrote: list[str] = []
    cached: list[str] = []
    failed: list[dict[str, str]] = []
    for src_pdf in sorted(figs.rglob("*.pdf")):
        # Compute the path relative to the source dir so the cache mirrors
        # the same layout (cache/figs/foo.pdf for figs/foo.pdf). That lets
        # \graphicspath{{.fig-cache/}} redirect \includegraphics{figs/foo.pdf}.
        try:
            rel = src_pdf.relative_to(source_dir)
        except ValueError:
            continue
        dest_pdf = cache / rel
        res = _sanitize_figure_pdf(src_pdf, dest_pdf, dry_run=dry_run)
        status = res.get("status")
        if status == "wrote":
            wrote.append(str(rel))
        elif status == "cached":
            cached.append(str(rel))
        elif status == "would-sanitize":
            wrote.append(str(rel))  # treat as planned-write for reporting
        else:
            failed.append({"path": str(rel), "error": res.get("error", "?")})
    return {"ok": not failed, "cache_dir": str(cache),
            "wrote": wrote, "cached": cached, "failed": failed}


def texinputs_prefix(source_dir: Path) -> str:
    """Return the TEXINPUTS path-prefix for the sanitized figure cache.

    The wrapper sets `\\graphicspath{{.fig-cache/}{./}}` for graphicx, so
    TEXINPUTS isn't strictly needed for graphics resolution. This helper is
    kept for callers that want to set TEXINPUTS for consistency.
    """
    return f"{source_dir}/{_SANITIZED_CACHE_SUBDIR}:"


# ────────────────────────────────────────────────────────────────────────────
# Artifact-link extraction
# ────────────────────────────────────────────────────────────────────────────
#
# The publication agent's editorial-summary is creative content (LLM-drafted).
# The artifact links beneath it should be deterministic: extracted directly
# from the paper's tex source, so we never *hallucinate* URLs.
#
# We pull:
#   - github.com/<org>/<repo> URLs  (code)
#   - osf.io/<id> URLs              (data / preregistrations)
#   - zenodo.org/record/<id> URLs   (data archives)
#   - huggingface.co/<…> URLs       (models / datasets)
#   - doi.org/<…> URLs              (data / papers)
#
# The caller adds project-specific entries (project page, reviews) separately.
_URL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Code (GitHub)",     re.compile(r"https?://github\.com/[\w\-.]+/[\w\-.]+(?:/[\w\-./]+)?", re.IGNORECASE)),
    ("Open Science Framework", re.compile(r"https?://osf\.io/\w+(?:/\w+)?", re.IGNORECASE)),
    ("Zenodo archive",    re.compile(r"https?://zenodo\.org/(?:record|deposit)/\d+", re.IGNORECASE)),
    ("Hugging Face",      re.compile(r"https?://huggingface\.co/[\w\-./]+", re.IGNORECASE)),
    ("DOI",               re.compile(r"https?://doi\.org/[\w./\-]+", re.IGNORECASE)),
]
# Trailing punctuation that's commonly part of a TeX url but not the URL itself.
_URL_TRAILING_TRIM = re.compile(r"[.,;:)\]}>]+$")


def extract_artifact_urls(tex_source: str) -> list[dict[str, str]]:
    """Scan a paper's TeX source for URLs we'd want to surface as artifacts.

    Returns a list of `{label, url}` dicts, deduped by URL (first occurrence
    wins, which preserves the order the author intended). Labels are derived
    from the URL host (e.g. github.com → "Code (GitHub)").

    Strips wrapping `\\url{...}`/`\\href{...}{...}` markup automatically since
    the raw URL pattern matches inside them.
    """
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for label, pat in _URL_PATTERNS:
        for m in pat.finditer(tex_source):
            url = _URL_TRAILING_TRIM.sub("", m.group(0))
            # Skip arxiv links if they're the paper's own arxiv id (caller
            # supplies that separately via --arxiv-id).
            if url in seen:
                continue
            seen.add(url)
            out.append({"label": label, "url": url})
    return out


def _strip_usepackage_lines(preamble: str, *,
                            class_provided: set[str] = _CLASS_PROVIDED_PACKAGES,
                            font_pkgs: set[str] = _FONT_PACKAGES,
                            layout_pkgs: set[str] = _LAYOUT_PACKAGES) -> tuple[str, list[str]]:
    """Comment out `\\usepackage` lines for packages the class already loads or
    that conflict with its typography. Returns (new_preamble, stripped_names).
    Comments out instead of deleting so the diff is reviewable."""
    stripped: list[str] = []
    to_strip = class_provided | font_pkgs | layout_pkgs
    out_lines: list[str] = []
    for line in preamble.splitlines(keepends=True):
        m = _USEPKG_RE.search(line)
        if m is None:
            out_lines.append(line)
            continue
        names = [n.strip() for n in m.group(1).split(",")]
        if any(n in to_strip for n in names):
            stripped.extend(n for n in names if n in to_strip)
            out_lines.append("% [llmxive-restyle] stripped: " + line)
        else:
            out_lines.append(line)
    return "".join(out_lines), stripped


def _strip_command_redefs(preamble: str) -> tuple[str, list[str]]:
    """Remove `\\renewcommand{\\maketitle}{...}` (the class defines its own).
    Returns (new_preamble, names_stripped). Best-effort; falls through if the
    regex can't match a balanced replacement (LaTeX brace-matching with regex
    has limits — for the common arxiv pattern this works)."""
    stripped: list[str] = []
    new = preamble
    if _MAKETITLE_REDEF_RE.search(new):
        new = _MAKETITLE_REDEF_RE.sub("% [llmxive-restyle] stripped custom \\\\maketitle redef\n", new)
        stripped.append("maketitle")
    return new, stripped


def _extract_metadata(preamble: str) -> dict[str, str]:
    """Pull \\title{}, \\author{}, \\date{} out of the preamble.

    For `\\author`: collect EVERY occurrence (handles the authblk style
    `\\author[1,2]{Name}` repeated per author). Joined with `\\and` so
    the class-level `\\authorblock` macro can split them downstream.
    """
    out = {}
    m = _TITLE_RE.search(preamble)
    if m:
        out["title"] = m.group(1).strip()
    authors = [a.strip() for a in _AUTHOR_RE.findall(preamble) if a.strip()]
    if authors:
        # If the paper used the single-author shape (one \author{X \and Y}),
        # there's one match containing the full block (already \\and-joined).
        # If it used authblk repeated (one match per author), join with \\and
        # so the downstream class can iterate them.
        out["author"] = " \\and ".join(authors)
    m = _DATE_RE.search(preamble)
    if m:
        out["date"] = m.group(1).strip()
    return out


def _strip_title_block(preamble: str) -> str:
    """Remove the original \\title / \\author / \\date / \\maketitle commands
    from the preamble (the wrapper redeclares them with our metadata)."""
    # Drop the \title / \author / \date themselves (we'll re-emit ours).
    # NOTE: re.sub treats the replacement string as a regex template — a
    # literal backslash needs `\\\\` to survive both Python string + regex
    # escaping. Easier: use a lambda to return a literal.
    preamble = _TITLE_RE.sub(
        lambda _: "% [llmxive-restyle] (original \\title moved to wrapper preamble)\n", preamble)
    preamble = _AUTHOR_RE.sub(
        lambda _: "% [llmxive-restyle] (original \\author moved to wrapper preamble)\n", preamble)
    preamble = _DATE_RE.sub(
        lambda _: "% [llmxive-restyle] (original \\date dropped — class uses metadata)\n", preamble)
    return preamble


# LaTeX special characters that need escaping in plain-text contexts (link
# labels, artifact captions). NOT applied to the editorial-summary body —
# that's already markdown; we convert headings + links and otherwise pass
# the prose through, on the assumption that the publication agent emits text
# safe for LaTeX (it should avoid `$`, `\`, `&`, `%`, `#`, `_`, `~`, `^`, `{`, `}` —
# we still escape those defensively).
_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _tex_escape(s: str) -> str:
    r"""Escape LaTeX specials in a plain-text fragment. Applied to artifact
    labels and to summary prose AFTER markdown links have been extracted —
    the URLs themselves go through `\href{...}` which tolerates them.
    Order matters: backslash first so we don't double-escape later replacements."""
    out = []
    for ch in s:
        out.append(_LATEX_ESCAPES.get(ch, ch))
    return "".join(out)


# Markdown subset: `## Heading` → `\edsection{Heading}`; `**bold**` → `\textbf{}`;
# `*italic*` / `_italic_` → `\textit{}`; `[label](url)` → `\href{url}{label}`.
_MD_HEADING_RE = re.compile(r"^\s*##\s+(.+?)\s*$", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# Bold/italic span across newlines but NOT across paragraph breaks (blank
# line). The DOTALL flag would let `.` match newlines; we use `[\s\S]` to
# keep the regex readable + still allow line wrapping inside the markup.
_MD_BOLD_RE = re.compile(r"\*\*([^*]+?)\*\*", re.DOTALL)
_MD_ITALIC_RE = re.compile(r"(?<![*\w])[*_]([^*_]+?)[*_](?![*\w])", re.DOTALL)


def _md_to_tex_summary(md: str) -> str:
    """Convert a small markdown subset (used in editorial summaries) to LaTeX.

    Supports:
      - `## Heading` lines  →  `\\edsection{Heading}`
      - `**bold**`          →  `\\textbf{bold}`
      - `*italic*`          →  `\\textit{italic}`
      - `[label](url)`      →  `\\href{url}{label}`
      - blank-line-separated paragraphs (no `\\par` needed; LaTeX handles them)

    Escapes other LaTeX specials in the surrounding prose. Designed for short
    editorial blurbs (a few paragraphs), not full papers.
    """
    # First, pull links + headings + bold + italic OUT as placeholders so the
    # generic escape doesn't mangle their syntax. We use sentinel tokens that
    # are vanishingly unlikely to appear in editorial prose.
    placeholders: dict[str, str] = {}

    # Sentinel uses only characters that pass through `_tex_escape` unchanged
    # (ASCII letters + digits + `@`). Underscores get escaped to `\_`, which
    # would break the lookup, so we avoid them in the key.
    def _stash(tag: str, value: str) -> str:
        key = f"LLMXAT{tag}AT{len(placeholders)}ATEND"
        placeholders[key] = value
        return key

    # 1. Links — replace with rendered \href{}{} (after escaping the label).
    def _link_sub(m: re.Match[str]) -> str:
        label = _tex_escape(m.group(1))
        url = m.group(2)
        return _stash("LINK", f"\\href{{{url}}}{{{label}}}")
    md = _MD_LINK_RE.sub(_link_sub, md)

    # 2. Bold and italic — also stash as rendered LaTeX so escapes don't touch them.
    md = _MD_BOLD_RE.sub(lambda m: _stash("B", f"\\textbf{{{_tex_escape(m.group(1))}}}"), md)
    md = _MD_ITALIC_RE.sub(lambda m: _stash("I", f"\\textit{{{_tex_escape(m.group(1))}}}"), md)

    # 3. Headings — `## Foo` becomes the edsection command.
    md = _MD_HEADING_RE.sub(lambda m: _stash("H", f"\\edsection{{{_tex_escape(m.group(1))}}}"), md)

    # 4. Escape what's left (plain prose), then restore the stashed commands.
    md = _tex_escape(md)
    for key, val in placeholders.items():
        md = md.replace(key, val)
    return md.strip()


def _render_artifacts(artifacts: list[dict[str, str]]) -> str:
    """Render a list of `{label, url}` dicts as a sequence of `\\edartifact{...}{...}`.
    Returns the inner content for `\\editorialartifacts{...}`."""
    lines: list[str] = []
    for art in artifacts:
        label = _tex_escape(art.get("label", "").strip())
        url = art.get("url", "").strip()
        if not (label and url):
            continue
        lines.append(f"  \\edartifact{{{label}}}{{{url}}}%")
    return "\n".join(lines)


def _load_artifacts(path: Path) -> list[dict[str, str]]:
    """Read a JSON file of artifact links. Format:
       [{"label": "Project folder", "url": "https://github.com/.../tree/main/projects/PROJ-XXX-..."},
        {"label": "Reviews", "url": "..."}, ...]

    Convention for the publication agent:
      - Use "Project folder" (not "Project page") and link to the *folder* in
        the GitHub repo under projects/PROJ-XXX-… — not to the original
        submission issue.
      - "Reviews" links to projects/PROJ-XXX-…/reviews/paper/ (or wherever
        the paper reviews live).
      - Only emit either of these *after* reviews have actually been
        generated (the script gates the entire artifact strip on whether
        an editorial summary was supplied — see restyle_paper).
    """
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"artifact-links file must be a JSON list, got {type(data).__name__}")
    out: list[dict[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        if "label" in entry and "url" in entry:
            out.append({"label": str(entry["label"]), "url": str(entry["url"])})
    return out


def restyle_paper(
    source_dir: Path,
    *,
    entry_tex: str = "main.tex",
    out_name: str = "main-llmxive.tex",
    arxiv_id: str | None = None,
    paper_status: str = "Preprint",
    paper_category: str = "Research paper",
    affiliation: str = "",
    correspondence: str = "",
    running_title: str = "",
    editorial_summary_md: str | None = None,
    editorial_summary_byline: str = "llmXive Editorial",
    artifact_links: list[dict[str, str]] | None = None,
    auto_extract_artifacts: bool = True,
    sanitize_figures: bool = True,
) -> dict[str, Any]:
    """Produce `<source_dir>/<out_name>` — an llmxive-class wrapper around the
    original `<source_dir>/<entry_tex>`. The body (everything between
    \\begin{document} and \\end{document}) is preserved EXACTLY; only the
    preamble + document class are rewritten.

    Returns a dict with `{ok, out_path, stripped_packages, stripped_redefs,
    metadata, body_bytes, error}`.
    """
    src = source_dir / entry_tex
    if not src.exists():
        return {"ok": False, "error": f"entry_tex not found: {src}"}

    # Sanitize figure PDFs into a sibling cache dir. The originals under
    # `figs/` are never touched; the lualatex compile picks up the cached
    # versions via a TEXINPUTS prefix (see texinputs_prefix() in this module).
    sanitize_result: dict[str, Any] = {"wrote": [], "cached": [], "failed": [], "cache_dir": ""}
    if sanitize_figures:
        sanitize_result = sanitize_figure_pdfs(source_dir)

    raw = src.read_text(encoding="utf-8", errors="replace")
    # Locate the document boundary.
    m_begin = _BEGIN_DOC_RE.search(raw)
    m_end = _END_DOC_RE.search(raw)
    if not m_begin or not m_end:
        return {"ok": False, "error": "could not find \\begin{document} / \\end{document}"}
    preamble = raw[:m_begin.start()]
    body = raw[m_begin.end():m_end.start()]   # everything between \begin{document} and \end{document}
    # Extract metadata BEFORE stripping the title block so we keep what was there.
    metadata = _extract_metadata(preamble)
    # Now clean the preamble: strip the package conflicts + the \maketitle redef
    # + the original title commands. Everything else (e.g. \newcommand aliases,
    # \newif, \newlength, custom math operators) is preserved verbatim so the
    # body's references still resolve.
    new_preamble, stripped_pkgs = _strip_usepackage_lines(preamble)
    new_preamble, stripped_redefs = _strip_command_redefs(new_preamble)
    new_preamble = _strip_title_block(new_preamble)
    # Drop a redundant leading \documentclass line (we re-emit it ourselves).
    new_preamble = _DOCCLASS_RE.sub(
        lambda _: "% [llmxive-restyle] (original \\documentclass replaced by wrapper)",
        new_preamble, count=1,
    )
    # Also drop the original \maketitle invocation (we'll emit it ourselves).
    # The body starts with \maketitle on its first line in most papers.
    body_lines = body.splitlines(keepends=True)
    new_body_lines: list[str] = []
    saw_maketitle = False
    for line in body_lines:
        if not saw_maketitle and re.match(r"\s*\\maketitle\b", line):
            new_body_lines.append("% [llmxive-restyle] (\\maketitle moved to wrapper)\n")
            saw_maketitle = True
        else:
            new_body_lines.append(line)
    new_body = "".join(new_body_lines)
    #
    # NOTE on figure-cache redirection: the body's `\includegraphics{figs/X.pdf}`
    # calls reference the original (Illustrator-broken) PDFs. We don't rewrite
    # those calls — instead, the llmxive class redefines `\includegraphics`
    # to consult `figs-sanitized/` first (see the class's `\renewcommand` on
    # `\includegraphics`). That keeps the BODY BYTES EXACTLY verbatim while
    # transparently picking up sanitized copies at compile time.

    # Editorial summary + artifact links — handed to the class as METADATA
    # (via `\seteditorialsummary` / `\seteditorialartifacts`) so the class can
    # render them inside the title block, guaranteeing they land on the title
    # page. The previous strategy of injecting an environment after `\maketitle`
    # produced page-1 overflow when the title block was tall.
    #
    # Artifact links: caller-supplied entries (project page, reviews, etc.) are
    # rendered first; auto-extracted URLs from the paper body (code, data, OSF,
    # HuggingFace, …) are appended afterward. This guarantees correctness for
    # project-specific links while still surfacing the resources the paper
    # itself points to — no hallucinated URLs.
    auto_artifacts: list[dict[str, str]] = []
    if auto_extract_artifacts:
        auto_artifacts = extract_artifact_urls(raw)
        # Dedupe against caller-supplied links by URL.
        if artifact_links:
            seen = {a["url"] for a in artifact_links}
            auto_artifacts = [a for a in auto_artifacts if a["url"] not in seen]

    combined_artifacts: list[dict[str, str]] = list(artifact_links or []) + auto_artifacts

    editorial_metadata_lines: list[str] = []
    if editorial_summary_md:
        summary_tex = _md_to_tex_summary(editorial_summary_md)
        editorial_metadata_lines.append(
            f"\\seteditorialbyline{{{_tex_escape(editorial_summary_byline)}}}"
        )
        editorial_metadata_lines.append(
            "\\seteditorialsummary{%\n" + summary_tex + "\n}"
        )
    # Gate the artifact strip on having an editorial summary. The user's rule
    # is that the title-page artifacts list belongs to the editorial summary —
    # without reviews/summary, no artifact strip on the PDF. (The website
    # still surfaces all artifacts in the project modal.)
    if combined_artifacts and editorial_summary_md:
        inner = _render_artifacts(combined_artifacts)
        if inner:
            editorial_metadata_lines.append(
                "\\seteditorialartifacts{%\n" + inner + "\n}"
            )
    editorial_metadata = "\n".join(editorial_metadata_lines)
    # No inline block any more — leave the body untouched. The class renders
    # the editorial summary inside the title block via the metadata above.
    editorial_block = ""

    # Build the wrapper. The preamble is sandwiched between our class +
    # metadata and the body's `\begin{document}` (which we re-emit).
    title = metadata.get("title", "Untitled")
    author = metadata.get("author", "")
    # `\runningtitle` defaults to \title if not set; allow the caller to override.
    runn = running_title or title
    # If the author has linebreaks (`\\`), keep them — the class's title block
    # handles a multi-line \author. If the author has a `Dartmouth College`
    # affiliation embedded after `\\`, the caller should pass `affiliation`
    # separately to clean it up.
    arxiv_line = f"\\paperid{{arXiv:{arxiv_id}}}\n" if arxiv_id else ""
    aff_line = f"\\affiliation{{{affiliation}}}\n" if affiliation else ""
    corr_line = f"\\correspondence{{{correspondence}}}\n" if correspondence else ""

    wrapper = f"""%% =====================================================================
%% {out_name} — auto-generated llmXive wrapper around {entry_tex}
%% =====================================================================
%% Generated by scripts/restyle_arxiv_paper.py. The original paper body is
%% copied below VERBATIM between \\begin{{document}} and \\end{{document}};
%% only the preamble + document class have changed. Do not hand-edit —
%% re-run the script if the source changes.
%%
%% Compile from the llmXive repo root:
%%   cd /path/to/llmXive
%%   TEXINPUTS=./papers/.style: xelatex \\
%%     -output-directory=<paper_pdf_dir> \\
%%     <this_file>
%%
%% Stripped packages (provided by llmxive.cls or font-conflicting):
%%   {", ".join(sorted(set(stripped_pkgs))) or "(none)"}
%% Stripped redefinitions:
%%   {", ".join(sorted(set(stripped_redefs))) or "(none)"}
%% =====================================================================
\\documentclass{{llmxive}}

%% ── llmXive paper metadata ─────────────────────────────────────────────
\\title{{{title}}}
\\author{{{author}}}
{aff_line}{corr_line}{arxiv_line}\\paperstatus{{{paper_status}}}
\\papercategory{{{paper_category}}}
\\runningtitle{{{runn}}}

%% ── Editorial summary + artifact links (rendered inside the title block
%% by the class so they appear on the title page).
{editorial_metadata}

%% (The class transparently redirects \\includegraphics calls to
%% figs-sanitized/* when those files exist — see the class's
%% \\renewcommand on \\includegraphics. No \\graphicspath needed.)

%% ── Original preamble (with conflicting packages commented out) ────────
{new_preamble}
%% ── BEGIN ORIGINAL BODY (preserved verbatim) ───────────────────────────
\\begin{{document}}
\\maketitle
{editorial_block}{new_body}\\end{{document}}
"""

    out_path = source_dir / out_name
    out_path.write_text(wrapper, encoding="utf-8")
    return {
        "ok": True,
        "out_path": str(out_path),
        "stripped_packages": sorted(set(stripped_pkgs)),
        "stripped_redefs": sorted(set(stripped_redefs)),
        "metadata": metadata,
        "body_bytes": len(new_body),
        "preamble_bytes": len(new_preamble),
        "sanitized_figures_wrote": sanitize_result.get("wrote", []),
        "sanitized_figures_cached": sanitize_result.get("cached", []),
        "sanitize_failures": sanitize_result.get("failed", []),
        "sanitize_cache_dir": sanitize_result.get("cache_dir", ""),
        "auto_extracted_artifacts": auto_artifacts,
        "combined_artifacts": combined_artifacts,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("source_dir", type=Path,
                    help="Directory containing the original main.tex + figures.")
    ap.add_argument("--entry", default="main.tex",
                    help="Original entry-point .tex file (default: main.tex).")
    ap.add_argument("--out", default="main-llmxive.tex",
                    help="Name of the generated wrapper .tex (default: main-llmxive.tex).")
    ap.add_argument("--arxiv-id", default=None, help="arXiv id (e.g. 2510.21958).")
    ap.add_argument("--paper-status", default="Preprint",
                    help="Paper status — Preprint | Peer Reviewed | Posted.")
    ap.add_argument("--paper-category", default="Research paper")
    ap.add_argument("--affiliation", default="",
                    help="\\affiliation{...} content; e.g. 'Dartmouth College'.")
    ap.add_argument("--correspondence", default="",
                    help="\\correspondence{...} content; e.g. 'jeremy@dartmouth.edu'.")
    ap.add_argument("--running-title", default="",
                    help="\\runningtitle{...}; defaults to the paper's \\title.")
    ap.add_argument("--editorial-summary", type=Path, default=None,
                    help="Path to a markdown file with the editorial summary "
                         "(drafted by the publication agent). Renders as an "
                         "eLife-style callout right after \\maketitle.")
    ap.add_argument("--editorial-byline", default="llmXive Editorial",
                    help="Byline shown in the editorial-summary callout "
                         "(default: 'llmXive Editorial').")
    ap.add_argument("--artifact-links", type=Path, default=None,
                    help="Path to a JSON file listing [{label, url}, ...] "
                         "for project artifacts (reviews, code, data, etc.) "
                         "to render under the editorial summary. "
                         "Project-specific entries; auto-extracted URLs from "
                         "the paper body are appended afterward.")
    ap.add_argument("--no-auto-extract", action="store_true",
                    help="Disable automatic extraction of artifact URLs "
                         "(github.com, osf.io, zenodo.org, huggingface.co, doi.org) "
                         "from the paper's TeX source. Default: extract.")
    ap.add_argument("--no-sanitize", action="store_true",
                    help="Disable ghostscript sanitization of figure PDFs "
                         "before compile. Default: sanitize "
                         "(workaround for Adobe Illustrator clipping bug).")
    args = ap.parse_args(argv)

    summary_md: str | None = None
    if args.editorial_summary is not None:
        if not args.editorial_summary.exists():
            print(f"[restyle] error: --editorial-summary not found: {args.editorial_summary}",
                  file=sys.stderr)
            return 2
        summary_md = args.editorial_summary.read_text(encoding="utf-8")

    artifacts: list[dict[str, str]] = []
    if args.artifact_links is not None:
        if not args.artifact_links.exists():
            print(f"[restyle] error: --artifact-links not found: {args.artifact_links}",
                  file=sys.stderr)
            return 2
        artifacts = _load_artifacts(args.artifact_links)

    res = restyle_paper(
        args.source_dir,
        entry_tex=args.entry,
        out_name=args.out,
        arxiv_id=args.arxiv_id,
        paper_status=args.paper_status,
        paper_category=args.paper_category,
        affiliation=args.affiliation,
        correspondence=args.correspondence,
        running_title=args.running_title,
        editorial_summary_md=summary_md,
        editorial_summary_byline=args.editorial_byline,
        artifact_links=artifacts,
        auto_extract_artifacts=not args.no_auto_extract,
        sanitize_figures=not args.no_sanitize,
    )
    if not res["ok"]:
        print(f"[restyle] error: {res.get('error')}", file=sys.stderr)
        return 2
    print(f"[restyle] wrote {res['out_path']}")
    print(f"[restyle]   stripped packages: {res['stripped_packages']}")
    print(f"[restyle]   stripped redefs: {res['stripped_redefs']}")
    print(f"[restyle]   preserved {res['body_bytes']:,} body bytes (verbatim)")
    n_wrote = len(res.get("sanitized_figures_wrote", []))
    n_cached = len(res.get("sanitized_figures_cached", []))
    if n_wrote or n_cached:
        cache_dir = res.get("sanitize_cache_dir", "")
        print(f"[restyle]   figure sanitization: wrote {n_wrote}, cached {n_cached}")
        print(f"[restyle]   cache dir: {cache_dir}")
        print(f"[restyle]   compile with: TEXINPUTS=\"{cache_dir}:papers/.style:\" lualatex ...")
    if res.get("sanitize_failures"):
        for f in res["sanitize_failures"]:
            print(f"[restyle]   WARNING: failed to sanitize {f['path']}: {f['error']}",
                  file=sys.stderr)
    if res.get("auto_extracted_artifacts"):
        print(f"[restyle]   auto-extracted {len(res['auto_extracted_artifacts'])} artifact URL(s) from paper body:")
        for a in res["auto_extracted_artifacts"]:
            print(f"[restyle]     - {a['label']}: {a['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
