"""Pipeline entry point.

Executes the full analysis workflow in the order required by the
specification:

1. Ingest / validation
2. Pre‑processing (filtering, CLR)
3. Per‑patient slope computation
4. Exploratory Spearman correlation
5. Linear Mixed‑Effects modelling
6. Permutation robustness test

The script respects the command‑line flags defined in the quickstart
documentation. It also propagates the ``skip`` flags produced by the
ingestion step (graceful degradation when the outcome column is missing).
In addition, it records wall‑clock timing for each pipeline stage,
writes a runtime log to ``data/results/runtime_log.txt`` and asserts that
the total wall‑clock time does not exceed 6 hours and that the permutation
step does not exceed 4 hours (SC‑003).
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

from llmxive_toolkit import get_logger, paths

# Import sub‑modules.
from . import ingest, preprocess, slopes, correlation, mixed_effects, permutation

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper for timing and logging each stage
# ----------------------------------------------------------------------
def _run_stage(name: str, func, *args, **kwargs):
    """Execute a pipeline stage, time it, and log the elapsed seconds.

    The elapsed time is written to the runtime log file
    ``data/results/runtime_log.txt`` as a simple ``<stage>: <seconds>`` line.
    """
    log.info("=== Starting stage: %s ===", name)
    start = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start
    log.info("=== Completed stage: %s (%.2f s) ===", name, elapsed)

    # Write timing entry
    runtime_path = paths.results("runtime_log.txt")
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{name}: {elapsed:.2f} seconds\n")

    return result, elapsed

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gut microbiome – PD progression pipeline")
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--max_taxa",
        type=int,
        default=100,
        help="Upper bound on taxa to retain (default: 100)",
    )
    parser.add_argument(
        "--perm_iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (default: 1000)",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # ------------------------------------------------------------------
    # 0. Global seed
    # ------------------------------------------------------------------
    np.random.seed(args.seed)

    # ------------------------------------------------------------------
    # Overall wall‑clock timer (SC‑003 total budget)
    # ------------------------------------------------------------------
    overall_start = time.time()

    # ------------------------------------------------------------------
    # 1. Ingest / validation
    # ------------------------------------------------------------------
    (ingest_res, _), _ = _run_stage("Ingest", ingest.main)

    if ingest_res != 0:
        log.error("Ingest step failed with exit code %s", ingest_res)
        return 1

    # Load validation report to respect skip flags.
    validation_path = paths.data("raw", "ingest_validation.json")
    validation = ingest.validate_inputs()  # fast re‑run for the dict
    skip = validation.get("skip_slope_and_correlation", False) or validation.get(
        "skip_mixed_effects", False
    )

    # ------------------------------------------------------------------
    # 2. Pre‑processing
    # ------------------------------------------------------------------
    (preprocess_summary, _), _ = _run_stage(
        "Preprocess", preprocess.run_preprocess, max_taxa=args.max_taxa
    )

    # ------------------------------------------------------------------
    # 3. Slope computation (may be skipped if outcome missing)
    # ------------------------------------------------------------------
    slope_elapsed = 0.0
    if not skip:
        (_, _), slope_elapsed = _run_stage(
            "Slope computation", slopes.run_slopes
        )
    else:
        log.info("Skipping slope, correlation, and mixed‑effects steps per skip flag.")

    # ------------------------------------------------------------------
    # 4. Correlation (Spearman)
    # ------------------------------------------------------------------
    corr_elapsed = 0.0
    if not skip:
        (_, _), corr_elapsed = _run_stage(
            "Correlation analysis", correlation.run_correlation
        )
    else:
        log.info("Skipping correlation step per skip flag.")

    # ------------------------------------------------------------------
    # 5. Mixed‑effects modelling
    # ------------------------------------------------------------------
    mixed_elapsed = 0.0
    if not skip:
        (_, _), mixed_elapsed = _run_stage(
            "Linear Mixed‑Effects modelling", mixed_effects.run_mixed_effects
        )
    else:
        log.info("Skipping mixed‑effects step per skip flag.")

    # ------------------------------------------------------------------
    # 6. Permutation robustness test
    # ------------------------------------------------------------------
    perm_elapsed = 0.0
    if not skip:
        (_, _), perm_elapsed = _run_stage(
            "Permutation robustness test",
            permutation.run_permutation,
            iterations=args.perm_iterations,
            seed=args.seed,
            max_wall_seconds=4 * 60 * 60,
        )
    else:
        log.info("Skipping permutation step per skip flag.")

    # ------------------------------------------------------------------
    # Total runtime check (SC‑003)
    # ------------------------------------------------------------------
    total_elapsed = time.time() - overall_start
    runtime_path = paths.results("runtime_log.txt")
    with runtime_path.open("a", encoding="utf-8") as fh:
        fh.write(f"Total: {total_elapsed:.2f} seconds\n")

    if total_elapsed > 6 * 60 * 60:
        log.error(
            "Total pipeline runtime %.2f seconds exceeds 6‑hour budget.", total_elapsed
        )
        raise AssertionError("Pipeline exceeded total wall‑clock budget of 6 hours.")

    if perm_elapsed > 4 * 60 * 60:
        log.error(
            "Permutation step runtime %.2f seconds exceeds 4‑hour budget.", perm_elapsed
        )
        raise AssertionError(
            "Permutation step exceeded wall‑clock budget of 4 hours."
        )

    log.info("Pipeline execution finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
