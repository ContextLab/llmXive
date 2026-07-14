"""
sensitivity.py

Performs a deterministic sensitivity analysis by sweeping the RANSAC
inlier‑threshold used in the sparse epipolar solver. For each threshold
the script recomputes the two primary evaluation metrics:

  * WorldScore (computed on the dense baseline)
  * Sparse‑Consistency Score (computed on the sparse warped frames)

The results are saved as a JSON file at ``data/results/sensitivity.json``.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from config import get_results_dir, ensure_directories
from eval.metrics import (
    calculate_world_score,
    calculate_sparse_consistency_score,
)

# ----------------------------------------------------------------------
# Helper loaders
# ----------------------------------------------------------------------
def _load_dense_baseline() -> np.ndarray:
    """Load the dense baseline frames from the standard location."""
    dense_path = Path("data") / "raw" / "dense_baseline_frames.npy"
    if not dense_path.is_file():
        raise FileNotFoundError(f"Dense baseline not found at {dense_path}")
    return np.load(dense_path, allow_pickle=False)


def _load_sparse_warped() -> np.ndarray:
    """Load the sparse warped frames produced by the geometry pipeline."""
    warped_path = Path("data") / "results" / "sparse_warped_frames.npy"
    if not warped_path.is_file():
        raise FileNotFoundError(f"Sparse warped frames not found at {warped_path}")
    return np.load(warped_path, allow_pickle=False)


# ----------------------------------------------------------------------
# Core pipeline runner
# ----------------------------------------------------------------------
def _run_geometry_pipeline(ransac_threshold: float) -> None:
    """
    Execute the full geometry pipeline (solver + warp) with a specific
    RANSAC inlier‑threshold.

    The pipeline script ``code/geometry/run_pipeline.py`` reads the
    environment variable ``RANSAC_THRESHOLD`` (if present) and uses it to
    configure the solver.  By invoking the script as a subprocess we keep
    the heavy computation isolated from the current process and ensure
    that any internal caching does not interfere between runs.
    """
    env = os.environ.copy()
    env["RANSAC_THRESHOLD"] = str(ransac_threshold)

    script_path = Path("code") / "geometry" / "run_pipeline.py"
    subprocess.run(
        [sys.executable, str(script_path)],
        check=True,
        env=env,
    )


# ----------------------------------------------------------------------
# Sensitivity sweep logic
# ----------------------------------------------------------------------
def run_ransac_sweep(
    thresholds: List[float],
) -> List[Tuple[float, float, float]]:
    """
    For each RANSAC inlier threshold, recompute the geometry pipeline
    and evaluate the two metrics.

    Returns a list of ``(threshold, world_score, sparse_consistency_score)``.
    """
    # WorldScore does not depend on the RANSAC threshold, so we load it once.
    dense_frames = _load_dense_baseline()
    world_score = calculate_world_score(dense_frames)

    results: List[Tuple[float, float, float]] = []

    for thr in thresholds:
        # Re‑run the geometry pipeline with the current threshold.
        # This overwrites ``data/results/sparse_warped_frames.npy`` with
        # the new result, which we then load to compute the sparse score.
        _run_geometry_pipeline(thr)

        # Load the newly‑produced sparse warped frames and compute the metric.
        sparse_frames = _load_sparse_warped()
        sparse_score = calculate_sparse_consistency_score(sparse_frames)

        results.append((thr, world_score, sparse_score))

    return results


def calculate_metrics_for_threshold(
    threshold: float,
    world_score: float,
    sparse_score: float,
) -> Dict[str, float]:
    """Package metrics for a single threshold into a serialisable dict."""
    return {
        "ransac_threshold": threshold,
        "world_score": world_score,
        "sparse_consistency_score": sparse_score,
    }


def run_sensitivity_sweep() -> List[Dict[str, float]]:
    """
    Orchestrates the full sweep and returns a list of metric dictionaries.
    """
    # Define a reasonable range of RANSAC thresholds (inlier pixel distance)
    thresholds = [0.5, 1.0, 1.5, 2.0, 2.5]
    raw_results = run_ransac_sweep(thresholds)

    return [
        calculate_metrics_for_threshold(thr, ws, ss)
        for (thr, ws, ss) in raw_results
    ]


def save_sensitivity_results(results: List[Dict[str, float]]) -> Path:
    """
    Write the sweep results to ``data/results/sensitivity.json``.
    Returns the path to the written file.
    """
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    out_path = results_dir / "sensitivity.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"Sensitivity results saved to {out_path}")
    return out_path


# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the sensitivity analysis and persist the results.
    """
    # ``ensure_directories`` tolerates being called without arguments.
    ensure_directories()
    results = run_sensitivity_sweep()
    save_sensitivity_results(results)


if __name__ == "__main__":
    main()
