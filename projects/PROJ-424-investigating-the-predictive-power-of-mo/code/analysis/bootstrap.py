import logging
import time
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from config import ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class BootstrapIterationResult:
    mean_mae: float
    ci_lower: float
    ci_upper: float

def load_mae_distribution(results: List[Dict], nist_refs: Dict[str, float]) -> List[float]:
    """Calculate MAE for each result."""
    maes = []
    for r in results:
        exp = nist_refs.get(r["solvent"], 0)
        if exp > 0:
            mae = abs(r["diffusion_coefficient"] - exp)
            maes.append(mae)
    return maes

def perform_bootstrap(maes: List[float], iterations: int) -> BootstrapIterationResult:
    """Perform bootstrap resampling."""
    if len(maes) == 0:
        return BootstrapIterationResult(0.0, 0.0, 0.0)
    
    means = []
    for _ in range(iterations):
        sample = np.random.choice(maes, size=len(maes), replace=True)
        means.append(np.mean(sample))
    
    mean_mae = np.mean(means)
    ci_lower = np.percentile(means, 2.5)
    ci_upper = np.percentile(means, 97.5)
    
    return BootstrapIterationResult(mean_mae, ci_lower, ci_upper)

def run_bootstrap_analysis(results: List[Dict], nist_refs: Dict[str, float]) -> Dict[str, Any]:
    """Run full bootstrap analysis with timeout check."""
    start_time = time.time()
    maes = load_mae_distribution(results, nist_refs)
    
    target_iter = ANALYSIS_CONFIG.bootstrap_iterations_target
    min_iter = ANALYSIS_CONFIG.bootstrap_min_iterations
    timeout = ANALYSIS_CONFIG.bootstrap_timeout_seconds
    
    current_iter = target_iter
    
    for i in range(target_iter):
        if time.time() - start_time > timeout:
            logger.warning(f"Bootstrap timeout reached at iteration {i}. Falling back to {min_iter}.")
            current_iter = min_iter
            break
    
    result = perform_bootstrap(maes, current_iter)
    
    return {
        "mean_mae": result.mean_mae,
        "ci_95_lower": result.ci_lower,
        "ci_95_upper": result.ci_upper,
        "iterations_performed": current_iter,
        "timeout_triggered": current_iter < target_iter
    }

def save_bootstrap_stats(stats: Dict[str, Any], output_dir: str):
    """Save bootstrap stats to CSV."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path = Path(output_dir) / "bootstrap_stats.csv"
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["mean_mae", stats["mean_mae"]])
        writer.writerow(["ci_95_lower", stats["ci_95_lower"]])
        writer.writerow(["ci_95_upper", stats["ci_95_upper"]])
        writer.writerow(["iterations", stats["iterations_performed"]])

def batch_bootstrap_analysis(results: List[Dict], nist_refs: Dict[str, float]):
    """Run bootstrap on the full batch."""
    return run_bootstrap_analysis(results, nist_refs)

def main():
    """Test bootstrap."""
    pass

if __name__ == "__main__":
    main()
