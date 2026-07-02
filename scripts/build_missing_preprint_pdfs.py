#!/usr/bin/env python3
"""Build missing/stale Reviewed-Preprint PDFs (CI sweep; needs TeX Live).

The reprocess drain runs on a runner WITHOUT TeX Live, so
``finalize_reviewed_preprint``'s best-effort ``build_preprint_pdfs`` fails
there and a cron-drained preprint lands with reviews but no themed PDFs.
This sweep runs inside the Paper Compile workflow (which installs TeX Live)
and builds, for every ``reviewed_preprint`` project:

- ``paper/pdf/original-llmxive.pdf``  (cover prepended to the untouched
  original; downloads the arXiv original when it isn't on disk), and
- ``paper/pdf/peer-review-llmxive.pdf`` (the automated-review report),

whenever either is MISSING or STALE (any review record is newer than the
report PDF). Idempotent; per-project failures are logged and skipped.

Usage: python scripts/build_missing_preprint_pdfs.py [--max N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llmxive.config import repo_root as _repo_root
from llmxive.paper_reprocess.preprint_pdf import build_preprint_pdfs
from llmxive.paper_reprocess.reprocess import project_dir
from llmxive.state import project as project_store
from llmxive.types import Stage


def needs_build(pdir: Path) -> bool:
    pdf_dir = pdir / "paper" / "pdf"
    original = pdf_dir / "original-llmxive.pdf"
    report = pdf_dir / "peer-review-llmxive.pdf"
    if not original.is_file() or not report.is_file():
        return True
    reviews = pdir / "paper" / "reviews"
    if reviews.is_dir():
        newest = max((f.stat().st_mtime for f in reviews.glob("*.md")), default=0.0)
        if newest > report.stat().st_mtime:
            return True  # reviews regenerated since the report was rendered
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max", type=int, default=10, help="max projects per sweep")
    args = ap.parse_args(argv)
    repo = _repo_root()

    built = failed = 0
    for proj in sorted(project_store.list_all(repo_root=repo), key=lambda p: p.id):
        if proj.current_stage != Stage.REVIEWED_PREPRINT:
            continue
        pdir = project_dir(proj, repo)
        if not (pdir / "paper" / "metadata.json").is_file():
            continue
        if not needs_build(pdir):
            continue
        try:
            out = build_preprint_pdfs(proj, repo_root=repo)
            print(f"built {proj.id}: original={bool(out['original'])} "
                  f"report={bool(out['peer_review'])}", flush=True)
            built += 1
        except Exception as exc:  # per-project failures never sink the sweep
            print(f"FAILED {proj.id}: {exc}", flush=True)
            failed += 1
        if built >= args.max:
            break
    print(f"sweep done: built={built} failed={failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
