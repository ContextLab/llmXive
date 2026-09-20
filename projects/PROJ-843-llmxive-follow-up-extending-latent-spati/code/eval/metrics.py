"""
Metrics Calculation (T017)

Computes WorldScore, Sparse-Consistency Score, and FID.
"""
import json
import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Local imports
from config import get_results_dir, get_raw_dir, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor

def calculate_world_score(warped_frames: Path, dense_baseline: Path) -> Optional[float]:
    """
    Calculate WorldScore (topological fidelity metric).
    
    Compares the warped frames against the dense baseline.
    """
    if not warped_frames.exists() or not dense_baseline.exists():
        return None
    
    try:
        warped = np.load(warped_frames)
        baseline = np.load(dense_baseline)
        
        if warped.size == 0 or baseline.size == 0:
            return None
        
        # Ensure same shape
        min_len = min(len(warped), len(baseline))
        warped = warped[:min_len]
        baseline = baseline[:min_len]
        
        # Compute topological fidelity (simplified: MSE)
        mse = np.mean((warped - baseline) ** 2)
        
        # Convert to score (0-1, higher is better)
        # Inverse relationship: lower MSE -> higher score
        score = 1.0 / (1.0 + mse)
        
        return float(score)
        
    except Exception as e:
        print(f"Error calculating WorldScore: {e}")
        return None

def calculate_sparse_consistency_score(warped_frames: Path, solver_output: Dict[str, Any]) -> Optional[float]:
    """
    Calculate Sparse-Consistency Score (re-projection error based).
    
    Uses the solver output to compute consistency.
    """
    if not warped_frames.exists():
        return None
    
    try:
        warped = np.load(warped_frames)
        
        if warped.size == 0:
            return None
        
        # Compute consistency from solver output
        # Simplified: use the average reprojection error from solver
        results = solver_output.get("results", [])
        
        if not results:
            return None
        
        errors = [r.get("reprojection_error", float('inf')) for r in results if r.get("status") == "success"]
        
        if not errors:
            return None
        
        avg_error = np.mean(errors)
        
        # Convert to score (0-1, higher is better)
        score = 1.0 / (1.0 + avg_error)
        
        return float(score)
        
    except Exception as e:
        print(f"Error calculating Sparse-Consistency Score: {e}")
        return None

def calculate_fid(warped_frames: Path, dense_baseline: Path) -> Optional[float]:
    """
    Calculate Fréchet Inception Distance (FID).
    
    Compares the distribution of warped frames against dense baseline.
    """
    if not warped_frames.exists() or not dense_baseline.exists():
        return None
    
    try:
        warped = np.load(warped_frames)
        baseline = np.load(dense_baseline)
        
        if warped.size == 0 or baseline.size == 0:
            return None
        
        # Simplified FID calculation (using pixel statistics)
        # In practice, use Inception-v3 features
        warped_mean = np.mean(warped, axis=(0, 1, 2))
        warped_cov = np.cov(warped.reshape(-1, warped.shape[-1]).T)
        
        baseline_mean = np.mean(baseline, axis=(0, 1, 2))
        baseline_cov = np.cov(baseline.reshape(-1, baseline.shape[-1]).T)
        
        # FID = ||mu1 - mu2||^2 + Tr(C1 + C2 - 2*sqrt(C1*C2))
        diff_mean = np.sum((warped_mean - baseline_mean) ** 2)
        
        # Simplified covariance term
        fid = diff_mean + np.trace(warped_cov + baseline_cov - 2 * np.sqrt(warped_cov @ baseline_cov + 1e-10))
        
        return float(fid)
        
    except Exception as e:
        print(f"Error calculating FID: {e}")
        return None

def compute_unified_geometric_error(warped_frames: Path, held_out_frames: Optional[Path] = None) -> Optional[float]:
    """
    Compute Unified Geometric Error (Photometric Consistency).
    
    Internal validation metric.
    """
    if not warped_frames.exists():
        return None
    
    try:
        warped = np.load(warped_frames)
        
        if warped.size == 0:
            return None
        
        # Compute geometric error (simplified: gradient magnitude consistency)
        # In practice, compare with held-out frames
        if held_out_frames and held_out_frames.exists():
            held_out = np.load(held_out_frames)
            min_len = min(len(warped), len(held_out))
            warped = warped[:min_len]
            held_out = held_out[:min_len]
            
            error = np.mean(np.abs(warped - held_out))
        else:
            # Internal consistency
            error = np.std(warped)
        
        return float(error)
        
    except Exception as e:
        print(f"Error computing Unified Geometric Error: {e}")
        return None

def aggregate_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate all metrics into a single report."""
    return {
        "world_score": metrics.get("world_score"),
        "sparse_consistency_score": metrics.get("sparse_consistency_score"),
        "fid": metrics.get("fid"),
        "unified_geometric_error": metrics.get("unified_geometric_error"),
        "timestamp": str(np.datetime64('now'))
    }

def main():
    """Main entry point for metrics calculation."""
    set_global_seed(42)
    
    results_dir = get_results_dir()
    raw_dir = get_raw_dir()
    ensure_directories(results_dir)
    
    # Paths
    warped_frames = results_dir / "sparse_warped_frames.npy"
    dense_baseline = raw_dir / "dense_baseline_frames.npy"
    
    # Calculate metrics
    metrics = {}
    
    print("Calculating WorldScore...")
    metrics["world_score"] = calculate_world_score(warped_frames, dense_baseline)
    
    print("Calculating Sparse-Consistency Score...")
    # Load solver output
    solver_path = results_dir / "geometry_outputs" / "solver_results.json"
    if solver_path.exists():
        with open(solver_path, 'r') as f:
            solver_output = json.load(f)
        metrics["sparse_consistency_score"] = calculate_sparse_consistency_score(warped_frames, solver_output)
    else:
        print("Solver output not found. Skipping Sparse-Consistency Score.")
    
    print("Calculating FID...")
    metrics["fid"] = calculate_fid(warped_frames, dense_baseline)
    
    print("Computing Unified Geometric Error...")
    metrics["unified_geometric_error"] = compute_unified_geometric_error(warped_frames)
    
    # Aggregate
    report = aggregate_metrics(metrics)
    
    # Save
    output_path = results_dir / "metrics.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Metrics saved to {output_path}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
