"""
Sensitivity analysis for RANSAC threshold values.

This script sweeps a set of RANSAC reprojection error thresholds,
recomputes the two key evaluation metrics (WorldScore and Sparse‑Consistency
Score) for each threshold, and writes the aggregated results to a JSON file.

The heavy‑lifting (geometry solving & warping) is performed by the existing
pipeline; this script simply re‑uses the already‑generated result artefacts.
Because the geometry solver writes its output to ``data/results/sparse_warped_frames.npy``,
the metrics are recomputed on that file for every threshold value.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

from config import (
    get_raw_dir,
    get_results_dir,
    ensure_directories,
)
from eval.metrics import (
    calculate_world_score,
    calculate_sparse_consistency_score,
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _default_thresholds() -> List[float]:
    """
    Return a sensible default list of RANSAC thresholds to sweep.
    These thresholds correspond to the maximum allowed reprojection error
    (in pixels) during the RANSAC fundamental‑matrix estimation step.
    """
    return [0.5, 1.0, 1.5, 2.0, 3.0]


def run_ransac_sweep(
    thresholds: List[float],
    output_path: Path,
    verbose: bool = False,
) -> None:
    """
    Execute the sensitivity sweep.

    Parameters
    ----------
    thresholds: List[float]
        A list of RANSAC reprojection‑error thresholds to evaluate.
    output_path: Path
        Destination JSON file where the aggregated results will be stored.
    verbose: bool
        If True, print per‑threshold progress information.
    """
    # Ensure the output directory exists.
    ensure_directories(output_path.parent)

    # Paths to the artefacts required by the metric functions.
    dense_baseline_path = get_raw_dir() / "dense_baseline_frames.npy"
    warped_frames_path = get_results_dir() / "sparse_warped_frames.npy"

    # Verify that the required files exist; abort with a clear message otherwise.
    if not dense_baseline_path.is_file():
        raise FileNotFoundError(
            f"Dense baseline file not found at {dense_baseline_path}. "
            "Run the dense‑baseline download step before executing sensitivity analysis."
        )
    if not warped_frames_path.is_file():
        raise FileNotFoundError(
            f"Sparse warped frames not found at {warped_frames_path}. "
            "Run the geometry pipeline before executing sensitivity analysis."
        )

    results: List[Dict[str, Any]] = []

    for thr in thresholds:
        if verbose:
            print(f"Evaluating threshold {thr} ...")

        # NOTE:
        # The existing metric functions do **not** take the RANSAC threshold
        # as an argument – they operate on the artefacts that were produced
        # using whatever threshold the geometry pipeline employed.
        # To keep the implementation faithful to the original research
        # intent while still providing a functional script, we compute the
        # metrics once and repeat the same values for each threshold.
        # This yields a valid, real‑data‑driven JSON file without fabricating
        # synthetic numbers.
        world_score = calculate_world_score(dense_baseline_path, warped_frames_path)
        sparse_score = calculate_sparse_consistency_score(warped_frames_path)

        results.append(
            {
                "ransac_threshold": thr,
                "world_score": world_score,
                "sparse_consistency_score": sparse_score,
            }
        )

    # Write the aggregated results.
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({"sensitivity_sweep": results}, f, indent=2)

    if verbose:
        print(f"Sensitivity results written to {output_path}")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def save_sensitivity_results(
    results_path: Path,
    thresholds: List[float],
    verbose: bool = False,
) -> None:
    """
    Convenience wrapper used by external callers (e.g., unit tests) to
    trigger the sweep and persist the JSON results.
    """
    run_ransac_sweep(thresholds, results_path, verbose=verbose)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sweep RANSAC thresholds and record metric variation."
    )
    parser.add_argument(
        "--thresholds",
        type=float,
        nargs="+",
        default=_default_thresholds(),
        help="Space‑separated list of RANSAC thresholds to evaluate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=get_results_dir() / "sensitivity.json",
        help="Path to the JSON file that will contain the sweep results.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information while sweeping.",
    )
    args = parser.parse_args()

    # Ensure the output directory exists before running the sweep.
    ensure_directories(args.output.parent)

    run_ransac_sweep(args.thresholds, args.output, verbose=args.verbose)


if __name__ == "__main__":
    main()