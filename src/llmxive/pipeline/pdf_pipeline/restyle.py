"""Spec 009 T053: deterministic arXiv-source -> llmxive-style restyle.

Orchestrates the three normalizers + injects \\documentclass{llmxive}. NO LLM.

Inputs:  a .tex source file (or directory of .tex sources)
Output:  rewritten .tex with normalized references / figures / authors.

If the source uses a custom formatting construct the class does not yet
support, the restyle emits a \\unsupportedblock{<name>}{...} which causes
lualatex to error LOUDLY (FR-020). The compile step surfaces that error.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import normalize_authors, normalize_figures, normalize_references

DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{[^}]+\}")

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
