"""Spec 009 T055: pdf_pipeline CLI entrypoint.

    python -m llmxive.pipeline.pdf_pipeline.cli build --source path/to/main.tex
    python -m llmxive.pipeline.pdf_pipeline.cli build --source-dir path/to/sources

No LLM. Deterministic. Uses SOURCE_DATE_EPOCH for byte-stable rebuilds.

By default we set SOURCE_DATE_EPOCH to a recent fixed instant (Jan 1 of the
current year) so the footer renders a sensible year — picking 0 (Unix epoch)
produces "1970" which is technically deterministic but reads as a defect.
Pass --source-date-epoch=N to override; --source-date-epoch=0 reproduces the
strict 1970-anchored byte-determinism used by tests.
"""

from __future__ import annotations

import argparse
import calendar
import shutil
import sys
import time
from pathlib import Path

from llmxive.config import repo_root as _repo_root

from .compile import compile_pdf
from .restyle import restyle_file


def _default_source_date_epoch() -> int:
    """Jan 1 of the current UTC year, as Unix seconds.

    Stable across rebuilds within the same calendar year, and renders the
    current year in \\the\\year-style footers.
    """
    year = time.gmtime().tm_year
    return calendar.timegm((year, 1, 1, 0, 0, 0, 0, 0, 0))


def _cmd_build(args: argparse.Namespace) -> int:
    src = Path(args.source).resolve()
    if not src.exists():
        sys.exit(f"FATAL: source not found: {src}")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage source directory contents into out_dir (so .cls, .bbl, .bib, figs/
    # etc. all travel with the .tex). The pipeline runs in `out_dir`; lualatex
    # needs every file referenced by the .tex to be reachable from there.
    src_dir = src.parent
    for child in src_dir.iterdir():
        # Skip the out dir itself if it lives under src_dir
        try:
            if child.resolve() == out_dir.resolve():
                continue
        except OSError:
            pass
        dest = out_dir / child.name
        if child.is_dir():
            if dest.exists():
                continue
            shutil.copytree(child, dest)
        else:
            if not dest.exists() or child.stat().st_mtime > dest.stat().st_mtime:
                shutil.copy2(child, dest)

    # If a llmxive.cls isn't already in the staging area, pull it from the
    # repo's papers/.style/ — Constitution I single-source-of-truth.
    cls_dest = out_dir / "llmxive.cls"
    if not cls_dest.exists():
        repo_cls = _repo_root() / "papers" / ".style" / "llmxive.cls"
        if repo_cls.exists():
            shutil.copy2(repo_cls, cls_dest)
        else:
            sys.exit(f"FATAL: llmxive.cls not found in source dir or {repo_cls}")

    # Spec 009: strip clobbering redefs (\newcommand{\todo} etc.) and pdflatex
    # primitives (\pdfoutput=1) from EVERY .tex file in the staged tree —
    # not just the main source — because publisher templates often \input
    # a preamble.tex that re-defines macros our class already shims.
    from .restyle import _strip_clobbering_redefs, _strip_pdflatex_primitives
    for tex in out_dir.rglob("*.tex"):
        try:
            text = tex.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new_text = _strip_pdflatex_primitives(_strip_clobbering_redefs(text))
        if new_text != text:
            tex.write_text(new_text, encoding="utf-8")

    staged_tex = out_dir / src.name
    restyled = restyle_file(staged_tex)
    pdf = compile_pdf(restyled, out_dir=out_dir, source_date_epoch=args.source_date_epoch)
    print(f"PDF: {pdf}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="llmxive-pdf", description="Deterministic arXiv-source -> PDF (no LLM)")
    sub = p.add_subparsers(dest="subcommand", required=True)
    sp = sub.add_parser("build", help="Restyle + compile one source")
    sp.add_argument("--source", required=True, help="Path to main .tex source")
    sp.add_argument("--out-dir", default=None, help="Output directory (default: source's parent)")
    sp.add_argument("--source-date-epoch", type=int, default=_default_source_date_epoch(),
                    help="SOURCE_DATE_EPOCH for byte-determinism (default: Jan 1 of current UTC year)")
    sp.set_defaults(handler=_cmd_build)
    return p


def main(argv: list[str] | None = None) -> int:
    return build_parser().parse_args(argv).handler(build_parser().parse_args(argv))


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(args.handler(args))
