import os
import json
import pickle
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from analysis.permutation_test import load_holdout_data, calculate_metric, run_permutation_test, calculate_p_value, save_holdout_metrics
from config import get_artifacts_path
from utils.logging import get_logger

logger = get_logger(__name__)

def run_reproducibility_check(
    model_path: str,
    holdout_data_path: str,
    n_permutations: int = 1000,
    seed: int = 42,
    metric: str = 'accuracy',
    tolerance: float = 1e-9
) -> Dict[str, Any]:
    """
    Runs the permutation test twice with the same seed to verify determinism.
    
    Args:
        model_path: Path to the trained model pickle file.
        holdout_data_path: Path to the holdout data CSV/JSON.
        n_permutations: Number of permutations to run.
        seed: Random seed for reproducibility.
        metric: Metric to evaluate ('accuracy', 'auc', etc.).
        tolerance: Floating point tolerance for comparison.
        
    Returns:
        Dictionary containing results from both runs and the reproducibility check status.
    """
    logger.info(f"Starting reproducibility check for permutation test with seed={seed}, n={n_permutations}")
    
    # Load data once
    X_holdout, y_holdout, model = load_holdout_data(model_path, holdout_data_path)
    
    # Run 1
    logger.info("Running permutation test iteration 1...")
    np.random.seed(seed)
    perm_results_1 = run_permutation_test(model, X_holdout, y_holdout, n_permutations, metric)
    p_value_1 = calculate_p_value(perm_results_1, y_holdout, metric)
    
    # Run 2
    logger.info("Running permutation test iteration 2...")
    np.random.seed(seed)
    perm_results_2 = run_permutation_test(model, X_holdout, y_holdout, n_permutations, metric)
    p_value_2 = calculate_p_value(perm_results_2, y_holdout, metric)
    
    # Compare
    is_identical = abs(p_value_1 - p_value_2) < tolerance
    diff = abs(p_value_1 - p_value_2)
    
    result = {
        "run_1": {
            "p_value": p_value_1,
            "observed_metric": perm_results_1.get('observed_metric'),
            "permutation_count": len(perm_results_1.get('permuted_metrics', []))
        },
        "run_2": {
            "p_value": p_value_2,
            "observed_metric": perm_results_2.get('observed_metric'),
            "permutation_count": len(perm_results_2.get('permuted_metrics', []))
        },
        "reproducibility": {
            "seed": seed,
            "tolerance": tolerance,
            "difference": diff,
            "is_identical": is_identical,
            "status": "PASS" if is_identical else "FAIL"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    if not is_identical:
        logger.error(f"Reproducibility check FAILED: p-value difference {diff} exceeds tolerance {tolerance}")
    else:
        logger.info(f"Reproducibility check PASSED: p-values identical within tolerance {tolerance}")
        
    return result

def save_reproducibility_report(result: Dict[str, Any], output_path: str) -> None:
    """Saves the reproducibility check result to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved reproducibility report to {output_path}")

def main() -> None:
    """Main entry point for the reproducibility check script."""
    config = {
        "model_path": os.path.join(get_artifacts_path(), "models", "final_model.pkl"),
        "holdout_data_path": os.path.join(get_artifacts_path(), "data", "holdout_data.csv"),
        "n_permutations": 1000,
        "seed": 42,
        "metric": "accuracy",
        "tolerance": 1e-9,
        "output_path": os.path.join(get_artifacts_path(), "reports", "permutation_reproducibility.json")
    }
    
    # Check if required files exist
    if not os.path.exists(config["model_path"]):
        logger.error(f"Model file not found: {config['model_path']}")
        return
        
    if not os.path.exists(config["holdout_data_path"]):
        logger.error(f"Holdout data file not found: {config['holdout_data_path']}")
        return
    
    result = run_reproducibility_check(**config)
    save_reproducibility_report(result, config["output_path"])
    
    if not result["reproducibility"]["is_identical"]:
        raise RuntimeError("Permutation test reproducibility check failed.")

if __name__ == "__main__":
    main()