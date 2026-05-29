"""Spec 009 T053: deterministic arXiv-source -> llmxive-style restyle.

Orchestrates the three normalizers + injects \\documentclass{llmxive} +
strips packages the class already provides. NO LLM.

Inputs:  a .tex source file (or directory of .tex sources)
Output:  rewritten .tex with normalized references / figures / authors.

If the source uses a custom formatting construct the class does not yet
support, the restyle emits a \\unsupportedblock{<name>}{...} which causes
lualatex to error LOUDLY (FR-020). The compile step surfaces that error.

Constitution I: package-stripping logic is imported from the legacy
scripts/restyle_arxiv_paper.py — that module owns the canonical
class-conflict-package list. We do NOT re-list packages here.
"""

from __future__ import annotations

import re
from pathlib import Path

from llmxive.config import repo_root as _repo_root

from . import normalize_authors, normalize_figures, normalize_references

DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}")
USEPKG_RE = re.compile(
    r"^\s*\\usepackage\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}\s*$",
    re.MULTILINE,
)

# Canonical list of packages the llmxive class already provides or that
# conflict with its setup. We attempt to import the legacy script's lists
# (Constitution I single-source-of-truth); fall back to a bundled copy if
# the legacy module can't be imported (e.g. invoked from a tarball).
try:
    import importlib.util as _iu
    _legacy_path = _repo_root() / "scripts" / "restyle_arxiv_paper.py"
    _spec = _iu.spec_from_file_location("_legacy_restyle", _legacy_path)
    _legacy = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_legacy)  # type: ignore
    _CONFLICT_PACKAGES = (
        _legacy._CLASS_PROVIDED_PACKAGES
        | _legacy._FONT_PACKAGES
        | _legacy._LAYOUT_PACKAGES
    )
except Exception:  # pragma: no cover — defensive
    _CONFLICT_PACKAGES = {
        "geometry", "hyperref", "caption", "titlesec", "fancyhdr", "xcolor",
        "microtype", "graphicx", "booktabs", "array", "tabularx", "colortbl",
        "amsmath", "amssymb", "amsthm", "mathtools", "enumitem", "listings",
        "fontenc", "inputenc", "url", "ragged2e", "etoolbox", "xparse",
        "calc", "tikz", "lastpage",
        "pxfonts", "txfonts", "mathptmx", "newtxtext", "newtxmath", "times",
        "mathpazo", "palatino", "helvet", "arev", "courier", "libertinus",
        "libertine", "inconsolata", "fontspec",
        "setspace", "lineno", "authblk", "todonotes", "tocloft",
    }

# Even when the legacy import succeeds we MUST also include the spec-009
# additions ("todonotes" / "tocloft" / etc.) — they're class-shim conflicts
# that the legacy script doesn't know about. Augment whatever we loaded.
_CONFLICT_PACKAGES = _CONFLICT_PACKAGES | {
    "todonotes", "tocloft",
    # algorithm + algorithmic are loaded by the class; strip from sources
    # to avoid double-load conflicts. algorithm2e and algpseudocode are
    # NOT stripped — papers using the mixed-case \Require/\State or KwIn
    # variants need them and our class doesn't load them.
    "algorithm", "algorithmic",
}


def _strip_class_conflict_packages(src: str, local_styles: set[str] | None = None) -> str:
    """Comment out \\usepackage lines for packages the class already provides.

    Identical semantics to the legacy script's `_strip_usepackage_lines`
    but applied to the full source (not just the preamble). The class
    will fail with "Option clash" or "already defined" errors otherwise
    (see FR-020 — silent fallback rendering is forbidden).

    ``local_styles``: names (without extension) of .sty/.cls files in the
    source directory. These are publisher templates (e.g. neurips_2026,
    colm2024_conference, llncs, mindlab) — they ALWAYS conflict with the
    llmxive class because they re-define everything. Strip them too.
    """
    extras = local_styles or set()
    all_conflicts = _CONFLICT_PACKAGES | extras

    def _sub(m: re.Match) -> str:
        names = [n.strip() for n in m.group(1).split(",")]
        if any(n in all_conflicts for n in names):
            return "% [llmxive-restyle] stripped: " + m.group(0).strip()
        return m.group(0)

    return USEPKG_RE.sub(_sub, src)


def _discover_local_styles(source_path: Path | str) -> set[str]:
    """Return names (sans extension) of every .sty/.cls in the source dir.

    These are publisher templates that ship alongside the paper source.
    Listed by spec FR-019 as "custom formatting constructs" — the deterministic
    pipeline must neutralise them since they conflict with the llmxive class.
    """
    p = Path(source_path)
    if p.is_file():
        p = p.parent
    if not p.is_dir():
        return set()
    return {
        f.stem for f in p.iterdir()
        if f.suffix in {".sty", ".cls"} and f.stem != "llmxive"
    }

# Constructs we do not yet support — re-mapped to \unsupportedblock so the
# compiler errors loudly. Grow this set as the registry needs (FR-022).
UNSUPPORTED_ENVS: list[str] = [
    # e.g. proprietary publisher classes' custom environments
    # "neuripsabstract", "aaaiabstract", ...
]


# Deterministic PDF trailer ID + suppression of optional metadata for SC-008.
# Injected immediately after \documentclass to make rebuilds byte-stable
# regardless of lualatex's random /ID generator.
_DETERMINISM_PREAMBLE = (
    "% [llmxive-restyle] deterministic PDF metadata (SC-008)\n"
    "\\directlua{\n"
    "  pdf.setsuppressoptionalinfo(\n"
    "    pdf.getsuppressoptionalinfo() | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512\n"
    "  )\n"
    "  pdf.settrailerid([[<00000000000000000000000000000000>"
    "<00000000000000000000000000000000>]])\n"
    "}\n"
)


def _inject_documentclass(src: str) -> str:
    """Replace the source's \\documentclass with \\documentclass{llmxive};
    inject deterministic-PDF preamble immediately after.
    """
    new_doc = r"\documentclass{llmxive}" + "\n" + _DETERMINISM_PREAMBLE
    if DOCUMENTCLASS_RE.search(src):
        # Use lambda to avoid backslash-in-replacement-as-backref issues
        return DOCUMENTCLASS_RE.sub(lambda _m: new_doc, src, count=1)
    # No documentclass — prepend
    return new_doc + src


def _wrap_unsupported(src: str) -> str:
    """Wrap any unsupported environment in \\unsupportedblock for loud failure."""
    for env in UNSUPPORTED_ENVS:
        pattern = re.compile(rf"\\begin\{{{env}\}}(.*?)\\end\{{{env}\}}", re.DOTALL)
        src = pattern.sub(
            lambda m, env=env: f"\\unsupportedblock{{{env}}}{{{m.group(1)}}}",
            src,
        )
    return src


_PDFLATEX_PRIMITIVE_RE = re.compile(
    r"^\s*\\pdfoutput\s*=\s*\d+\s*$",
    re.MULTILINE,
)
# Commands like \newcommand{\todo}{...} that re-define what some packages
# (notably todonotes) provide globally; if the source's local override
# arrives after a publisher class has already defined \todo, lualatex
# crashes with "already defined". Strip the source-side override; the
# class's no-op compatibility shim handles the basic case.
_CLOBBERS_RE = re.compile(
    r"^\s*\\newcommand\s*\*?\s*\{?\\(?:todo|titlerunning|authorrunning|institute|inst|correspondingauthor|equalcontrib|AND|And|theHalgorithm|AT|maketitle)\}?[^\n]*\n",
    re.MULTILINE,
)
# Source-side \newtheorem{theorem}{...} clobbers the class's preregistered
# theorem environments. Strip the most common ones; if a paper actually uses
# a custom theorem env (e.g. `claim`), it still goes through.
_NEWTHEOREM_RE = re.compile(
    r"^\s*\\newtheorem\s*\{(?:theorem|lemma|proposition|corollary|definition|remark|example|proof)\}[^\n]*\n",
    re.MULTILINE,
)


def _strip_pdflatex_primitives(src: str) -> str:
    """Strip pdflatex-only primitives that crash lualatex."""
    return _PDFLATEX_PRIMITIVE_RE.sub("", src)


def _strip_clobbering_redefs(src: str) -> str:
    """Strip source-side redefinitions of commands we provide as shims."""
    src = _CLOBBERS_RE.sub("", src)
    src = _NEWTHEOREM_RE.sub("", src)
    return src


def restyle_source(src: str, *, local_styles: set[str] | None = None) -> str:
    """Apply all restyle steps to a LaTeX source string. Idempotent.

    ``local_styles``: names of local .sty/.cls files in the source dir
    (publisher templates). Strip them so they don't conflict with the
    llmxive class.
    """
    out = src
    out = _strip_pdflatex_primitives(out)
    out = _strip_clobbering_redefs(out)
    out = normalize_references.normalize(out)
    out = normalize_figures.normalize(out)
    out = normalize_authors.normalize(out)
    out = _wrap_unsupported(out)
    out = _strip_class_conflict_packages(out, local_styles=local_styles)
    out = _inject_documentclass(out)
    return out


def restyle_file(in_path: Path | str, out_path: Path | str | None = None) -> Path:
    """Read in_path, restyle, write to out_path (defaults to <in>-llmxive.tex).

    Auto-discovers local .sty/.cls publisher templates next to the source
    and strips their \\usepackage{} lines from the restyled output.
    """
    in_path = Path(in_path)
    if not in_path.exists():
        raise FileNotFoundError(in_path)
    out_path = Path(out_path) if out_path else in_path.with_name(in_path.stem + "-llmxive.tex")
    local_styles = _discover_local_styles(in_path.parent)
    out_path.write_text(
        restyle_source(in_path.read_text(encoding="utf-8"), local_styles=local_styles),
        encoding="utf-8",
    )
    return out_path
