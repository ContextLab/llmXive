"""Spec 009 T054: deterministic lualatex + bibtex compile.

Fail-fast precondition: `lualatex` and `bibtex` MUST be on PATH (Principle V).
Sets SOURCE_DATE_EPOCH for byte-determinism per SC-008.

NO LLM imports — enforced by T014 AST guard.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _check_tools() -> None:
    for tool in ("lualatex", "bibtex"):
        if shutil.which(tool) is None:
            raise RuntimeError(
                f"FATAL: required tool {tool!r} not on PATH. "
                "Install MacTeX / TeX Live."
            )


def compile_pdf(tex_path: Path | str, *, out_dir: Path | str | None = None,
                source_date_epoch: int = 0) -> Path:
    """Compile a .tex to .pdf deterministically. Returns the PDF path.

    Two-pass lualatex + bibtex + lualatex + lualatex schedule per the
    standard reference-resolution dance.
    """
    _check_tools()
    tex_path = Path(tex_path)
    if not tex_path.exists():
        raise FileNotFoundError(tex_path)
    out_dir = Path(out_dir) if out_dir else tex_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = str(source_date_epoch)
    env["TZ"] = "UTC"
    # FORCE_SOURCE_DATE makes lualatex respect SOURCE_DATE_EPOCH for \today etc.
    env["FORCE_SOURCE_DATE"] = "1"

    def _run(cmd: list[str]) -> None:
        result = subprocess.run(
            cmd, cwd=str(out_dir), env=env,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout[-2000:]}"
                f"\nSTDERR:\n{result.stderr[-2000:]}"
            )

    # Make sure the tex source is reachable from out_dir
    rel = tex_path.resolve()
    base = rel.stem

    # Pass 1
    _run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", str(rel)])
    # Bibtex (best-effort: a paper with no \cite{} won't have an .aux ref list)
    aux = out_dir / f"{base}.aux"
    if aux.exists() and "\\bibdata" in aux.read_text():
        _run(["bibtex", base])
        _run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", str(rel)])
    # Final pass to resolve cross-refs
    _run(["lualatex", "-interaction=nonstopmode", "-halt-on-error", str(rel)])

    pdf = out_dir / f"{base}.pdf"
    if not pdf.exists():
        raise RuntimeError(f"compile completed without errors but PDF not found: {pdf}")
    return pdf
