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
    # 1. Ingest / validation
    # ------------------------------------------------------------------
    log.info("=== Phase 0: Input validation ===")
    try:
        ingest_code = ingest.main()
    except SystemExit as e:
        log.error("Ingest failed with exit code %s", e.code)
        return 1
    if ingest_code != 0:
        log.error("Ingest returned non‑zero code %s", ingest_code)
        return 1

    # Load validation report to respect skip flags.
    validation_path = paths.data("raw", "ingest_validation.json")
    validation = ingest.validate_inputs()  # re‑run to get dict (fast)
    skip = validation.get("skip_slope_and_correlation", False) or validation.get(
        "skip_mixed_effects", False
    )

    # ------------------------------------------------------------------
    # 2. Pre‑processing
    # ------------------------------------------------------------------
    log.info("=== Phase 1: Pre‑processing ===")
    preprocess_summary = preprocess.run_preprocess(max_taxa=args.max_taxa)

    # ------------------------------------------------------------------
    # 3. Slope computation (may be skipped if outcome missing)
    # ------------------------------------------------------------------
    if not skip:
        log.info("=== Phase 2: Slope computation ===")
        slopes.run_slopes()
    else:
        log.info("Skipping slope, correlation, and mixed‑effects steps per skip flag.")

    # ------------------------------------------------------------------
    # 4. Correlation (Spearman)
    # ------------------------------------------------------------------
    if not skip:
        log.info("=== Phase 3: Correlation analysis ===")
        correlation.run_correlation()
    else:
        log.info("Skipping correlation step per skip flag.")

    # ------------------------------------------------------------------
    # 5. Mixed‑effects modelling
    # ------------------------------------------------------------------
    if not skip:
        log.info("=== Phase 4: Linear Mixed‑Effects modelling ===")
        mixed_effects.run_mixed_effects()
    else:
        log.info("Skipping mixed‑effects step per skip flag.")

    # ------------------------------------------------------------------
    # 6. Permutation robustness test
    # ------------------------------------------------------------------
    if not skip:
        log.info("=== Phase 5: Permutation robustness test ===")
        start = time.time()
        permutation.run_permutation(
            iterations=args.perm_iterations,
            seed=args.seed,
            max_wall_seconds=4 * 60 * 60,
        )
        log.info("Permutation step completed in %.2f seconds", time.time() - start)
    else:
        log.info("Skipping permutation step per skip flag.")

    log.info("Pipeline execution finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
