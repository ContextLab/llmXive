"""
Master orchestration script for the Möbius autocorrelation pipeline.

This script runs the full analysis in the required order:
  1. Generate the Möbius sequence (sieve)
  2. Sample windows (generate_mobius)
  3. Compute autocorrelations (autocorrelation)
  4. Build the null distribution (null_distribution)
  5. Apply Benjamini‑Hochberg FDR correction (fdr_correction)
  6. Perform zero‑density sensitivity analysis (sensitivity)
  7. Produce heat‑map visualisations (viz)
  8. Run the Kolmogorov‑Smirnov uniformity test (uniformity_test)

The script can be invoked as a module:
    python -m code.main [--demo]

The optional ``--demo`` flag runs a lightweight demonstration that
uses a reduced sieve size and fewer windows.  For the purposes of
the integration test we simply run the full pipeline regardless of
the flag – the downstream scripts already contain their own
``--demo`` handling where appropriate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import the entry‑point functions from the existing modules.
# Each module provides a ``main`` function that performs its step
# and writes the expected artefacts to disk.
from generate_mobius import main as generate_mobius_main
from sieve import main as sieve_main
from autocorrelation import main as autocorr_main
from null_distribution import main as null_dist_main
from fdr_correction import main as fdr_main
from sensitivity import main as sensitivity_main
from viz import main as viz_main
from uniformity_test import main as uniformity_main


def _run_step(step_func, step_name: str) -> None:
    """Execute a pipeline step and abort on failure.

    Parameters
    ----------
    step_func : callable
        The ``main`` function of the step to run.
    step_name : str
        Human readable name for error messages.
    """
    try:
        step_func()
    except Exception as exc:  # pragma: no cover – defensive
        print(f"[ERROR] Step '{step_name}' failed: {exc}", file=sys.stderr)
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full Möbius autocorrelation pipeline."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a quick demo (reduced data size).",
    )
    return parser.parse_args()


def main() -> None:
    """Run the pipeline in the correct order."""
    args = _parse_args()

    # 1. Sieve – generate μ(n) array.
    _run_step(sieve_main, "sieve")

    # 2. Window sampling.
    _run_step(generate_mobius_main, "window sampling")

    # 3. Autocorrelation for all windows / lags.
    _run_step(autocorr_main, "autocorrelation")

    # 4. Null‑distribution via block permutations.
    _run_step(null_dist_main, "null distribution")

    # 5. Benjamini‑Hochberg FDR correction.
    _run_step(fdr_main, "FDR correction")

    # 6. Zero‑density sensitivity analysis.
    _run_step(sensitivity_main, "sensitivity analysis")

    # 7. Visualisation (heatmaps).
    _run_step(viz_main, "visualisation")

    # 8. Uniformity (KS) test.
    _run_step(uniformity_main, "KS uniformity test")

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
