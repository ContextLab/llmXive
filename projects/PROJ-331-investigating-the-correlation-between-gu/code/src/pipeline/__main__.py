"""Pipeline entry point (Task T001‑T006 orchestration)."""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from llmxive_toolkit import paths

from . import ingest, preprocess, slopes, correlation, mixed_effects, permutation

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

STAGE_ORDER = [
    ("Ingest", ingest.main),
    ("Preprocess", preprocess.main),
    ("Slope computation", slopes.main),
    ("Correlation analysis", correlation.main),
    ("Linear Mixed‑Effects modelling", mixed_effects.main),
    ("Permutation robustness test", permutation.main),
]


def _run_stage(log_path: Path, name: str, func, *args, **kwargs):
    start = time.time()
    rc = func(*args, **kwargs)
    elapsed = time.time() - start
    # Append timing info
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{name}: {elapsed:.2f} seconds\\n")
    return rc, elapsed


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full gut‑microbiome PD pipeline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max_taxa", type=int, default=100, help="Maximum taxa after RAM cap")
    parser.add_argument(
        "--perm_iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (0 to skip)",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv)

    # Runtime log path
    log_path = paths.results("runtime_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Run stages sequentially, capturing elapsed times
    timings = {}
    rc, elapsed = _run_stage(log_path, "Ingest", ingest.main)
    if rc != 0:
        return rc
    timings["Ingest"] = elapsed

    rc, elapsed = _run_stage(log_path, "Preprocess", preprocess.main)
    if rc != 0:
        return rc
    timings["Preprocess"] = elapsed

    rc, elapsed = _run_stage(log_path, "Slope computation", slopes.main)
    if rc != 0:
        return rc
    timings["Slope computation"] = elapsed

    rc, elapsed = _run_stage(log_path, "Correlation analysis", correlation.main)
    if rc != 0:
        return rc
    timings["Correlation analysis"] = elapsed

    rc, elapsed = _run_stage(log_path, "Linear Mixed‑Effects modelling", mixed_effects.main)
    if rc != 0:
        return rc
    timings["Linear Mixed‑Effects modelling"] = elapsed

    # Permutation step may be skipped via zero iterations
    if args.perm_iterations > 0:
        rc, elapsed = _run_stage(
            log_path,
            "Permutation robustness test",
            permutation.main,
            iterations=args.perm_iterations,
            seed=args.seed,
        )
        if rc != 0:
            return rc
        timings["Permutation robustness test"] = elapsed
    else:
        timings["Permutation robustness test"] = 0.0

    # Total runtime assertion (SC‑003)
    total_time = sum(timings.values())
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"Total: {total_time:.2f} seconds\\n")
    if total_time > 6 * 60 * 60:
        logger.error("Pipeline exceeded total wall‑clock budget of 6 hours.")
        return 1
    if timings.get("Permutation robustness test", 0) > 4 * 60 * 60:
        logger.error("Permutation step exceeded its 4‑hour wall‑clock budget.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
