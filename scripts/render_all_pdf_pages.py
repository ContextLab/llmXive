"""Render every page of every PDF under docs/papers/PROJ-*/*.pdf to PNGs.

Used during the spec-010 iterative audit loop to support a visual sweep
of every page (the user's instruction: "carefully go through *all* PDFs
(screenshots of each page!) and use this to flag and correct any issues
with the pdf rendering/compiling pipeline").

Output structure:
    state/audit/pdf/<YYYY-MM-DD>/screenshots/<paper-id>/p001.png
                                                       p002.png
                                                       ...

NO LLM CALLS — pure pdftoppm rasterization, consistent with the
no-LLM constraint on the PDF pipeline (FR-013, spec 010).

Usage:
    python scripts/render_all_pdf_pages.py [--papers-dir docs/papers]
                                           [--out-root state/audit/pdf]
                                           [--dpi 100]
                                           [--only PROJ-NNN-...]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def render_pdf(pdf_path: Path, out_dir: Path, dpi: int) -> int:
    """Render every page of `pdf_path` to PNGs under `out_dir`/p001.png ...

    Returns the number of pages rendered.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    # pdftoppm writes <prefix>-<N>.png with N starting at 1.
    prefix = out_dir / "p"
    cmd = [
        "pdftoppm",
        "-r", str(dpi),
        "-png",
        str(pdf_path),
        str(prefix),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"FAIL {pdf_path}: pdftoppm returned {proc.returncode}: {proc.stderr.strip()}",
              file=sys.stderr)
        return 0
    pages = sorted(out_dir.glob("p-*.png"))
    # Normalize filenames to p001.png, p002.png so they sort lexically.
    for i, p in enumerate(pages, start=1):
        new = out_dir / f"p{i:03d}.png"
        if p != new:
            p.rename(new)
    return len(list(out_dir.glob("p*.png")))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--papers-dir", default="docs/papers", help="directory of PROJ-*/*.pdf")
    p.add_argument("--out-root", default="state/audit/pdf", help="audit root dir")
    p.add_argument("--dpi", type=int, default=100, help="render DPI (default 100)")
    p.add_argument("--only", default=None, help="paper-id substring filter; renders only matching PDFs")
    args = p.parse_args(argv)

    if shutil.which("pdftoppm") is None:
        print("error: pdftoppm not found on PATH; install poppler", file=sys.stderr)
        return 2

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    shots_root = Path(args.out_root) / today / "screenshots"

    papers_dir = Path(args.papers_dir)
    if not papers_dir.is_dir():
        print(f"error: papers-dir not a directory: {papers_dir}", file=sys.stderr)
        return 2

    pdfs = sorted(papers_dir.glob("PROJ-*/main-llmxive.pdf"))
    if args.only:
        pdfs = [p for p in pdfs if args.only in str(p)]
    if not pdfs:
        print(f"no PDFs matched under {papers_dir}", file=sys.stderr)
        return 0

    total_pages = 0
    for pdf in pdfs:
        paper_id = pdf.parent.name
        out_dir = shots_root / paper_id
        n = render_pdf(pdf, out_dir, dpi=args.dpi)
        total_pages += n
        print(f"  {paper_id}: {n} page(s) → {out_dir}")
    print(f"rendered {total_pages} page(s) across {len(pdfs)} PDF(s) under {shots_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
