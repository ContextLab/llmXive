"""
Sensitivity Analysis for RANSAC Thresholds.

Re-executes the geometry solver (T010) for specific RANSAC thresholds
and reports the variation in WorldScore and Sparse-Consistency Score.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Local imports
from config import (
    get_results_dir,
    get_features_dir,
    get_ransac_threshold,
    set_ransac_threshold,
    ensure_directories,
    get_config_summary
)
from geometry.solver import run_solver
from geometry.warp import run_warp_pipeline
from geometry.aggregate_warps import aggregate_warped_frames, load_unsolvable_list
from eval.metrics import calculate_world_score, calculate_sparse_consistency_score
from utils.memory_monitor import MemoryMonitor
from utils.seeds import set_global_seed

# Thresholds to sweep as per task description
RANSAC_THRESHOLDS = [0.01, 0.05, 0.1]
OUTPUT_FILE = "sensitivity_analysis.json"

def run_ransac_sweep(
    thresholds: List[float],
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Re-execute the solver and warp pipeline for each threshold.

    Args:
        thresholds: List of RANSAC thresholds to test.
        output_dir: Directory to write intermediate results for this sweep.

    Returns:
        Dictionary containing results for each threshold.
    """
    results = {}
    features_dir = get_features_dir()
    results_base = get_results_dir() if output_dir is None else output_dir

    # Ensure output directory exists
    ensure_directories(results_base)

    print(f"Starting RANSAC Threshold Sweep: {thresholds}")
    print(f"Features directory: {features_dir}")
    print(f"Results directory: {results_base}")

    # Check if features exist
    if not features_dir.exists():
        raise FileNotFoundError(f"Features directory not found: {features_dir}. "
                                "Run T009 (extract_features) first.")

    # Check for existing features
    feature_files = list(features_dir.glob("*.npy"))
    if not feature_files:
        # Try json as well
        feature_files = list(features_dir.glob("*.json"))

    if not feature_files:
        raise FileNotFoundError(f"No feature files found in {features_dir}. "
                                "Run T009 (extract_features) first.")

    print(f"Found {len(feature_files)} feature files.")

    # Store original threshold to restore later
    original_threshold = get_ransac_threshold()

    try:
        for threshold in thresholds:
            print(f"\n{'='*40}")
            print(f"Processing Threshold: {threshold}")
            print(f"{'='*40}")

            # Update global config for this run
            set_ransac_threshold(threshold)

            # Create a temporary results subdirectory for this threshold
            # to avoid overwriting previous results until complete
            threshold_dir = results_base / f"threshold_{threshold}"
            ensure_directories(threshold_dir)

            # 1. Run Solver
            print("Running Solver...")
            # We need to pass the specific directory to solver to avoid global state issues
            # However, run_solver uses global config for paths. We assume it respects the
            # set_ransac_threshold call.
            try:
                unsolvable_path = solver_main_output = run_solver(
                    features_dir=features_dir,
                    output_dir=threshold_dir
                )
                print(f"Solver complete. Unsolvable list: {unsolvable_path}")
            except Exception as e:
                print(f"Solver failed for threshold {threshold}: {e}")
                # If solver fails completely (e.g. no inliers), record as failure
                results[threshold] = {
                    "status": "failed",
                    "error": str(e),
                    "world_score": None,
                    "sparse_consistency_score": None
                }
                continue

            # 2. Run Warp
            print("Running Warp...")
            try:
                warp_output = run_warp_pipeline(
                    features_dir=features_dir,
                    output_dir=threshold_dir
                )
                print(f"Warp complete. Output: {warp_output}")
            except Exception as e:
                print(f"Warp failed for threshold {threshold}: {e}")
                results[threshold] = {
                    "status": "failed",
                    "error": str(e),
                    "world_score": None,
                    "sparse_consistency_score": None
                }
                continue

            # 3. Aggregate Warped Frames
            print("Aggregating Warped Frames...")
            try:
                # load_unsolvable_list expects a path, aggregate_warped_frames writes to output
                unsolvable_list = load_unsolvable_list(
                    unsolvable_path=threshold_dir / "unsolvable_sequences.json"
                )
                print(f"Loaded {len(unsolvable_list)} unsolvable sequences.")

                aggregated_path = aggregate_warped_frames(
                    warped_frames_dir=threshold_dir / "warped_frames",
                    unsolvable_list=unsolvable_list,
                    output_path=threshold_dir / "sparse_warped_frames.npy"
                )
                print(f"Aggregation complete. Output: {aggregated_path}")
            except Exception as e:
                print(f"Aggregation failed for threshold {threshold}: {e}")
                results[threshold] = {
                    "status": "failed",
                    "error": str(e),
                    "world_score": None,
                    "sparse_consistency_score": None
                }
                continue

            # 4. Compute Metrics
            print("Computing Metrics...")
            metrics = {
                "status": "success",
                "threshold": threshold
            }

            # Load dense baseline for WorldScore comparison
            dense_baseline_path = Path("data/raw/dense_baseline_frames.npy")
            if not dense_baseline_path.exists():
                print(f"Warning: Dense baseline not found at {dense_baseline_path}. "
                      "Skipping WorldScore calculation.")
                metrics["world_score"] = None
            else:
                try:
                    ws = calculate_world_score(
                        sparse_warped_path=aggregated_path,
                        dense_baseline_path=dense_baseline_path
                    )
                    metrics["world_score"] = float(ws)
                    print(f"WorldScore: {ws:.4f}")
                except Exception as e:
                    print(f"WorldScore calculation failed: {e}")
                    metrics["world_score"] = None

            # Compute Sparse-Consistency Score
            try:
                scs = calculate_sparse_consistency_score(
                    warped_frames_path=aggregated_path
                )
                metrics["sparse_consistency_score"] = float(scs)
                print(f"Sparse-Consistency Score: {scs:.4f}")
            except Exception as e:
                print(f"Sparse-Consistency Score calculation failed: {e}")
                metrics["sparse_consistency_score"] = None

            results[threshold] = metrics

    finally:
        # Restore original threshold
        set_ransac_threshold(original_threshold)

    return results

def save_sensitivity_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save sensitivity analysis results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Sensitivity results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run RANSAC threshold sensitivity analysis.")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory for results. Defaults to data/results/")
    args = parser.parse_args()

    # Set seed for reproducibility
    set_global_seed(42)

    output_dir = Path(args.output) if args.output else get_results_dir()
    ensure_directories(output_dir)

    try:
        results = run_ransac_sweep(RANSAC_THRESHOLDS, output_dir)
        output_file = output_dir / OUTPUT_FILE
        save_sensitivity_results(results, output_file)

        # Print summary
        print("\n" + "="*50)
        print("SENSITIVITY ANALYSIS SUMMARY")
        print("="*50)
        print(f"{'Threshold':<15} {'WorldScore':<20} {'Sparse-Consistency':<20} {'Status'}")
        print("-"*75)
        for threshold, data in results.items():
            ws = data.get("world_score", "N/A")
            scs = data.get("sparse_consistency_score", "N/A")
            status = data.get("status", "unknown")
            if isinstance(ws, float): ws = f"{ws:.4f}"
            if isinstance(scs, float): scs = f"{scs:.4f}"
            print(f"{threshold:<15} {str(ws):<20} {str(scs):<20} {status}")
        print("="*50)

    except Exception as e:
        print(f"Error in sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
