"""US3 pipeline runner (Task T008c).

Executes the User-Story-3 stages in order:

    T001 ingest -> T002 preprocess -> T003 slopes -> T005 mixed-effects
    -> T006 permutation robustness

producing ``data/results/mixed_effects_summary.csv`` and
``data/results/permutation_pvalues.csv``, with per-stage timings
appended to ``data/results/runtime_log.txt``.

The permutation stage is bounded by a 4-hour wall-clock guard
(FR-007 / SC-003); the total run is asserted to stay within 6 hours.

The pipeline operates only on the researcher-supplied raw inputs under
``data/raw/``. If they are absent, the ingest stage aborts loudly with
a ``FileNotFoundError`` -- no synthetic fallback is ever performed.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List

from llmxive_toolkit import get_logger, paths

from . import ingest, mixed_effects, permutation, preprocess, slopes

log = get_logger(__name__)

PERMUTATION_BUDGET_SECONDS = 4 * 60 * 60  # FR-007
TOTAL_BUDGET_SECONDS = 6 * 60 * 60  # SC-003


def _log_stage(log_path: Path, name: str, seconds: float) -> None:
    """Append a ``<stage>: <seconds>`` line to the runtime log."""
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}: {seconds:.2f}\n")


def _run_stage(log_path: Path, name: str, func, *args, **kwargs):
    """Time one pipeline stage, log it, and return its result."""
    start = time.time()
    log.info("=== US3 stage %s started ===", name)
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    _log_stage(log_path, f"us3_{name}", elapsed)
    log.info("=== US3 stage %s finished in %.2f s ===", name, elapsed)
    return result


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the US3 (permutation robustness) pipeline."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (default: 1000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for the permutation test (default: 42).",
    )
    parser.add_argument(
        "--max_wall_seconds",
        type=int,
        default=PERMUTATION_BUDGET_SECONDS,
        help="Wall-time budget for the permutation stage (default: 4 h).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)
    log_path = paths.results("runtime_log.txt")
    total_start = time.time()

    # ---- T001: ingest / input validation (aborts loudly if data missing)
    _run_stage(log_path, "ingest", ingest.main)

    # ---- T002: filtering, CLR transformation (FR-002, FR-003, FR-010)
    _run_stage(log_path, "preprocess", preprocess.run_preprocess)

    # ---- T003: per-patient slopes (FR-004 prerequisite)
    _run_stage(log_path, "slopes", slopes.run_slopes)

    # ---- T005: linear mixed-effects modeling (FR-005, FR-006)
    mixed_csv = _run_stage(log_path, "mixed_effects", mixed_effects.run_mixed_effects)
    if not Path(mixed_csv).is_file():
        log.error("Mixed-effects summary was not written: %s", mixed_csv)
        return 1

    # ---- T006: permutation robustness (FR-007) with 4-hour guard
    perm_start = time.time()
    perm_csv = _run_stage(
        log_path,
        "permutation",
        permutation.run_permutation,
        iterations=args.iterations,
        seed=args.seed,
        max_wall_seconds=args.max_wall_seconds,
    )
    perm_elapsed = time.time() - perm_start
    if perm_elapsed > args.max_wall_seconds:
        log.error(
            "Permutation stage breached its %.0f s wall-time budget "
            "(took %.2f s). Partial results were written to %s.",
            args.max_wall_seconds,
            perm_elapsed,
            perm_csv,
        )
    if not Path(perm_csv).is_file():
        log.error("Permutation results were not written: %s", perm_csv)
        return 1

    total_elapsed = time.time() - total_start
    _log_stage(log_path, "us3_total", total_elapsed)
    log.info(
        "US3 pipeline complete: total %.2f s (permutation %.2f s). "
        "Deliverables: %s, %s",
        total_elapsed,
        perm_elapsed,
        mixed_csv,
        perm_csv,
    )
    if total_elapsed > TOTAL_BUDGET_SECONDS:
        log.error(
            "Total US3 wall-time %.2f s exceeded the 6-hour budget.",
            total_elapsed,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
