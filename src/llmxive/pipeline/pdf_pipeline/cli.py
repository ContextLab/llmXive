"""Spec 009 T055: pdf_pipeline CLI entrypoint.

    python -m llmxive.pipeline.pdf_pipeline.cli build --source path/to/main.tex
    python -m llmxive.pipeline.pdf_pipeline.cli build --source-dir path/to/sources

No LLM. Deterministic. Use SOURCE_DATE_EPOCH for byte-stable rebuilds.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from .compile import compile_pdf
from .restyle import restyle_file


def _cmd_build(args: argparse.Namespace) -> int:
    src = Path(args.source).resolve()
    if not src.exists():
        sys.exit(f"FATAL: source not found: {src}")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage source into out_dir
    staged = out_dir / src.name
    if staged.resolve() != src.resolve():
        shutil.copy(src, staged)
    restyled = restyle_file(staged)
    pdf = compile_pdf(restyled, out_dir=out_dir, source_date_epoch=args.source_date_epoch)
    print(f"PDF: {pdf}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="llmxive-pdf", description="Deterministic arXiv-source -> PDF (no LLM)")
    sub = p.add_subparsers(dest="subcommand", required=True)
    sp = sub.add_parser("build", help="Restyle + compile one source")
    sp.add_argument("--source", required=True, help="Path to main .tex source")
    sp.add_argument("--out-dir", default=None, help="Output directory (default: source's parent)")
    sp.add_argument("--source-date-epoch", type=int, default=0,
                    help="SOURCE_DATE_EPOCH for byte-determinism (default 0)")
    sp.set_defaults(handler=_cmd_build)
    return p


def main(argv: list[str] | None = None) -> int:
    return build_parser().parse_args(argv).handler(build_parser().parse_args(argv))


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(args.handler(args))
