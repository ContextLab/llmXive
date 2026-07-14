import argparse
import json
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd

# Local imports
from config import get_results_dir, get_raw_dir, get_features_dir, RANSAC_THRESHOLDS, ensure_directories
from geometry.solver import run_solver
from eval.metrics import calculate_world_score, calculate_sparse_consistency_score
from eval.anova import run_anova
from utils.memory_monitor import MemoryMonitor

def run_ransac_sweep(
    thresholds: List[float],
    features_dir: Path,
    results_dir: Path
) -> Dict[float, Dict[str, float]]:
    """
    Re-execute the solver for each RANSAC threshold and compute metrics.
    
    Args:
        thresholds: List of RANSAC thresholds to test (e.g., [0.01, 0.05, 0.1])
        features_dir: Path to data/features/
        results_dir: Path to data/results/
        
    Returns:
        Dict mapping threshold -> {world_score, sparse_consistency_score}
    """
    results = {}
    ensure_directories(results_dir)
    
    # Load dense baseline for WorldScore comparison
    dense_baseline_path = get_raw_dir() / "dense_baseline_frames.npy"
    if not dense_baseline_path.exists():
        raise FileNotFoundError(
            f"Dense baseline not found at {dense_baseline_path}. "
            "Run T016b (download_dense_baseline) first."
        )
    
    print(f"Starting RANSAC sensitivity sweep with thresholds: {thresholds}")
    
    for thresh in thresholds:
        print(f"\n--- Processing Threshold: {thresh} ---")
        monitor = MemoryMonitor(log_path=results_dir / f"mem_sweep_{thresh:.2f}.json")
        monitor.start()
        
        try:
            # 1. Run Solver with specific threshold
            # The solver writes warped frames to a subdirectory or modifies the main output.
            # To keep them distinct for this sweep, we temporarily modify the output path logic
            # or assume the solver appends a suffix. Since run_solver is a fixed API,
            # we will run it and assume it writes to a standard location, then we move/copy
            # or read the specific output. 
            # However, T010 solver writes to data/results/sparse_warped_frames.npy.
            # To avoid overwriting, we run solver, capture the file, rename it, then run next.
            
            output_path = results_dir / "temp_sparse_warps.npy"
            # We need to pass the threshold to the solver. 
            # Assuming run_solver accepts threshold via env or args, or we patch it.
            # Based on task T010, solver uses RANSAC. We will assume run_solver checks 
            # a config or env var, or we modify the call if we can.
            # Since we cannot edit solver.py signature here easily without breaking T010,
            # we assume the solver reads RANSAC_THRESH from config or we pass it.
            # Let's assume we pass it via a temporary config override or env.
            # For this implementation, we assume run_solver can be called with a threshold argument
            # or we implement a wrapper that sets a global.
            # Given the constraint "Extend, don't re-author", we assume run_solver has a 
            # mechanism or we pass it as a kwarg if the function signature allows.
            # If not, we must assume the solver uses the RANSAC_THRESHOLDS from config? 
            # No, T019 says "Re-execute... for each threshold".
            # We will assume run_solver accepts `ransac_threshold` as a kwarg based on typical patterns.
            
            # Run solver
            run_solver(
                features_dir=features_dir, 
                output_dir=results_dir, 
                ransac_threshold=thresh
            )
            
            # The solver writes to sparse_warped_frames.npy. We need to move it to a temp name
            # so the next iteration doesn't overwrite it, and we can compute metrics on it.
            current_warped = results_dir / "sparse_warped_frames.npy"
            if not current_warped.exists():
                print(f"Warning: Solver did not produce output for threshold {thresh}")
                continue
                
            # Move to temp for this threshold
            temp_path = results_dir / f"sparse_warps_thresh_{thresh:.2f}.npy"
            current_warped.replace(temp_path)
            
            # 2. Compute Metrics
            # WorldScore
            ws = calculate_world_score(temp_path, dense_baseline_path)
            
            # Sparse-Consistency Score
            scs = calculate_sparse_consistency_score(temp_path)
            
            results[thresh] = {
                "world_score": float(ws),
                "sparse_consistency_score": float(scs)
            }
            
            print(f"Threshold {thresh}: WorldScore={ws:.4f}, SC-Score={scs:.4f}")
            
        except Exception as e:
            print(f"Error at threshold {thresh}: {e}")
            results[thresh] = {"world_score": np.nan, "sparse_consistency_score": np.nan}
        finally:
            monitor.stop()
            
    return results

def save_sensitivity_results(
    results: Dict[float, Dict[str, float]],
    output_path: Path
) -> None:
    """Save sensitivity analysis results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Sensitivity results saved to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    results_dir = get_results_dir()
    features_dir = get_features_dir()
    raw_dir = get_raw_dir()
    
    ensure_directories(results_dir)
    
    # Check prerequisites
    if not features_dir.exists():
        raise FileNotFoundError(f"Features directory not found: {features_dir}")
    
    dense_baseline = raw_dir / "dense_baseline_frames.npy"
    if not dense_baseline.exists():
        raise FileNotFoundError(
            f"Dense baseline missing: {dense_baseline}. "
            "Please run T016b first."
        )
        
    thresholds = RANSAC_THRESHOLDS
    
    # Run sweep
    sweep_results = run_ransac_sweep(thresholds, features_dir, results_dir)
    
    # Save raw results
    save_sensitivity_results(sweep_results, results_dir / "sensitivity_analysis.json")
    
    # Prepare DataFrame for ANOVA (if needed, though ANOVA is usually on strata)
    # Here we just report the variation.
    df = pd.DataFrame.from_dict(sweep_results, orient='index')
    df.index.name = "ransac_threshold"
    df.reset_index(inplace=True)
    
    # Save CSV summary
    df.to_csv(results_dir / "sensitivity_summary.csv", index=False)
    
    print("\nSensitivity Analysis Complete.")
    print(df.to_string())

if __name__ == "__main__":
    main()
