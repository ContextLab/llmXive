"""Pipeline entry point for the Gut Microbiome – PD Progression analysis.

This script orchestrates the full analysis workflow, timing each stage and
writing a simple runtime log to ``data/results/runtime_log.txt``. The
stages executed are:

1. Ingest – validate raw inputs.
2. Preprocess – filtering, CLR transformation and optional taxa capping.
3. Slope computation – per‑patient taxon and clinical outcome slopes.
4. Correlation analysis – Spearman correlation with BH correction.
5. Linear Mixed‑Effects modelling – interaction term per taxon.
6. Permutation robustness test – empirical p‑values.

The command‑line interface mirrors the one described in ``quickstart.md``:

.. code-block:: bash

    python -m code.src.pipeline \\
        --seed 42 \\
        --max_taxa 100 \\
        --perm_iterations 1000

All default file locations follow the project conventions and are
automatically created by the helper functions in the respective modules.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List

import numpy as np

# Pipeline stage imports
from src.pipeline import ingest, preprocess, slopes, correlation, mixed_effects, permutation
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities (unchanged signatures)
# ----------------------------------------------------------------------


def _run_stage(log_path: Path, name: str, func, *args, **kwargs):
    """Execute a pipeline stage, time it, and log the elapsed seconds.

    The elapsed time is written to ``data/results/runtime_log.txt`` as a
    simple ``<stage>: <seconds>`` line.
    """
    start = time.time()
    result = func(*args, **kwargs)
    seconds = time.time() - start
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{name}: {seconds:.2f} seconds\n")
    log.info("%s completed in %.2f seconds", name, seconds)
    return result


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments for the full pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the full Gut Microbiome – PD progression pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--max_taxa",
        type=int,
        default=100,
        help="Upper bound on taxa retained after filtering (default: 100).",
    )
    parser.add_argument(
        "--perm_iterations",
        type=int,
        default=1000,
        help="Number of permutation iterations (default: 1000).",
    )
    return parser.parse_args(argv)


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    """Execute the full pipeline.

    Returns:
        int: Exit code (0 for success, non‑zero for failure).
    """
    args = _parse_args(argv)

    # Ensure reproducibility for all stochastic steps.
    np.random.seed(args.seed)

    # Runtime log file – created lazily by the first stage.
    runtime_log = paths.results("runtime_log.txt")

    # ------------------------------------------------------------------
    # Stage 1 – Ingest
    # ------------------------------------------------------------------
    try:
        _run_stage(runtime_log, "Ingest", ingest.main)
    except Exception as exc:
        log.error("Ingest stage failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Stage 2 – Preprocess
    # ------------------------------------------------------------------
    try:
        _run_stage(
            runtime_log,
            "Preprocess",
            preprocess.run_preprocess,
            max_taxa=args.max_taxa,
        )
    except Exception as exc:
        log.error("Preprocess stage failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Stage 3 – Slope computation
    # ------------------------------------------------------------------
    try:
        taxon_slopes_path, outcome_slopes_path = _run_stage(
            runtime_log, "Slope computation", slopes.run_slopes
        )
    except Exception as exc:
        log.error("Slope computation stage failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Stage 4 – Correlation analysis (plain Spearman + BH)
    # ------------------------------------------------------------------
    try:
        _run_stage(
            runtime_log,
            "Correlation analysis",
            correlation.run_correlation,
            partial=False,
            taxon_slopes_path=taxon_slopes_path,
            outcome_slopes_path=outcome_slopes_path,
        )
    except Exception as exc:
        log.error("Correlation stage failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Stage 5 – Linear Mixed‑Effects modelling
    # ------------------------------------------------------------------
    try:
        _run_stage(
            runtime_log,
            "Linear Mixed‑Effects modelling",
            mixed_effects.run_mixed_effects,
        )
    except Exception as exc:
        log.error("Mixed‑effects stage failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Stage 6 – Permutation robustness test
    # ------------------------------------------------------------------
    try:
        _run_stage(
            runtime_log,
            "Permutation robustness test",
            permutation.run_permutation,
            iterations=args.perm_iterations,
            seed=args.seed,
        )
    except Exception as exc:
        log.error("Permutation stage failed: %s", exc)
        return 1

    # ------------------------------------------------------------------
    # Total runtime
    # ------------------------------------------------------------------
    total_seconds = sum(
        float(line.split(":")[1].strip().split()[0])
        for line in runtime_log.read_text(encoding="utf-8").splitlines()
        if ":" in line
    )
    with open(runtime_log, "a", encoding="utf-8") as f:
        f.write(f"Total: {total_seconds:.2f} seconds\n")
    log.info("Pipeline completed – total time %.2f seconds", total_seconds)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())