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
    _legacy_path = Path(__file__).resolve().parents[4] / "scripts" / "restyle_arxiv_paper.py"
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
        "setspace", "lineno", "authblk",
    }


def _strip_class_conflict_packages(src: str) -> str:
    """Comment out \\usepackage lines for packages the class already provides.

    Identical semantics to the legacy script's `_strip_usepackage_lines`
    but applied to the full source (not just the preamble). The class
    will fail with "Option clash" or "already defined" errors otherwise
    (see FR-020 — silent fallback rendering is forbidden).
    """
    def _sub(m: re.Match) -> str:
        names = [n.strip() for n in m.group(1).split(",")]
        if any(n in _CONFLICT_PACKAGES for n in names):
            return "% [llmxive-restyle] stripped: " + m.group(0).strip()
        return m.group(0)

    return USEPKG_RE.sub(_sub, src)

# Constructs we do not yet support — re-mapped to \unsupportedblock so the
# compiler errors loudly. Grow this set as the registry needs (FR-022).
UNSUPPORTED_ENVS: list[str] = [
    # e.g. proprietary publisher classes' custom environments
    # "neuripsabstract", "aaaiabstract", ...
]


def _inject_documentclass(src: str) -> str:
    """Replace the source's \\documentclass with \\documentclass{llmxive}."""
    if DOCUMENTCLASS_RE.search(src):
        return DOCUMENTCLASS_RE.sub(r"\\documentclass{llmxive}", src, count=1)
    # No documentclass — prepend
    return r"\documentclass{llmxive}" + "\n" + src


def _wrap_unsupported(src: str) -> str:
    """Wrap any unsupported environment in \\unsupportedblock for loud failure."""
    for env in UNSUPPORTED_ENVS:
        pattern = re.compile(rf"\\begin\{{{env}\}}(.*?)\\end\{{{env}\}}", re.DOTALL)
        src = pattern.sub(
            lambda m, env=env: f"\\unsupportedblock{{{env}}}{{{m.group(1)}}}",
            src,
        )
    return src


def restyle_source(src: str) -> str:
    """Apply all restyle steps to a LaTeX source string. Idempotent."""
    out = src
    out = normalize_references.normalize(out)
    out = normalize_figures.normalize(out)
    out = normalize_authors.normalize(out)
    out = _wrap_unsupported(out)
    out = _strip_class_conflict_packages(out)
    out = _inject_documentclass(out)
    return out


def restyle_file(in_path: Path | str, out_path: Path | str | None = None) -> Path:
    """Read in_path, restyle, write to out_path (defaults to <in>-llmxive.tex)."""
    in_path = Path(in_path)
    if not in_path.exists():
        raise FileNotFoundError(in_path)
    out_path = Path(out_path) if out_path else in_path.with_name(in_path.stem + "-llmxive.tex")
    out_path.write_text(restyle_source(in_path.read_text(encoding="utf-8")), encoding="utf-8")
    return out_path
