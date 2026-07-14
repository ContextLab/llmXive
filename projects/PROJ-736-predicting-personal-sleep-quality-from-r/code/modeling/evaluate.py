"""
Evaluation module for User Story 2.
Implements bootstrap resampling of outer-fold predictions to estimate R² confidence intervals.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Local imports based on API surface
from config import get_paths, ensure_dirs, get_hyperparameter
from utils.logging import get_logger, log_stage_start, log_stage_complete, log_stage_error, LogEntry
from utils.metrics import r_squared

# Global state for graceful shutdown
_SHUTDOWN_EVENT = threading.Event()
_RESULTS_BUFFER: Optional[List[Dict[str, Any]]] = None
_OUTPUT_PATH: Optional[str] = None

def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM to flush partial results."""
    if _RESULTS_BUFFER is not None and _OUTPUT_PATH is not None:
        try:
            with open(_OUTPUT_PATH, 'w') as f:
                json.dump({"bootstrap_samples": _RESULTS_BUFFER, "status": "interrupted"}, f, indent=2)
            print(f"Interrupted. Partial results saved to {_OUTPUT_PATH}")
        except Exception as e:
            print(f"Failed to save partial results: {e}")
    sys.exit(1)

import threading

def load_predictions(predictions_path: str = "data/processed/predictions.npy") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load outer-fold predictions, true values, and subject IDs.
    Returns: (predictions, y_true, subject_ids)
    """
    logger = get_logger()
    log_stage_start(logger, "Loading Data")
    
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found at {predictions_path}. "
                                "Run code/modeling/train.py first to generate this file.")
    
    data = np.load(predictions_path, allow_pickle=True).item()
    predictions = data['predictions']
    y_true = data['y_true']
    subject_ids = data.get('subject_ids', np.arange(len(y_true)))
    
    log_stage_complete(logger, "Data loaded")
    return predictions, y_true, subject_ids

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² score."""
    return r_squared(y_true, y_pred)

def bootstrap_resample_r2(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_iterations: int = 1000,
    random_state: int = 42
) -> List[float]:
    """
    Perform bootstrap resampling to generate a distribution of R² scores.
    
    Args:
        y_true: True values.
        y_pred: Predicted values.
        n_iterations: Number of bootstrap resamples.
        random_state: Random seed for reproducibility.
        
    Returns:
        List of R² scores from each bootstrap iteration.
    """
    logger = get_logger()
    log_stage_start(logger, "Bootstrap Resampling (1000 iterations)")
    
    rng = np.random.default_rng(random_state)
    n_samples = len(y_true)
    bootstrap_scores = []
    
    start_time = time.time()
    for i in range(n_iterations):
        if _SHUTDOWN_EVENT.is_set():
            break
            
        # Resample indices with replacement
        indices = rng.choice(n_samples, size=n_samples, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        
        # Calculate R² for this resample
        r2 = calculate_r2(y_true_boot, y_pred_boot)
        bootstrap_scores.append(r2)
        
        # Progress logging every 100 iterations
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            logger.log_operation("bootstrap_progress", iteration=i+1, elapsed_seconds=elapsed)
    
    log_stage_complete(logger, f"Bootstrap complete. Generated {len(bootstrap_scores)} samples.")
    return bootstrap_scores

def save_bootstrap_results(
    bootstrap_scores: List[float],
    output_path: str = "data/results/bootstrap_ci.json",
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Save bootstrap results and calculate confidence intervals.
    
    Args:
        bootstrap_scores: List of R² scores from bootstrap iterations.
        output_path: Path to save results.
        confidence_level: Confidence level for CI (default 0.95).
        
    Returns:
        Dictionary containing CI results and statistics.
    """
    logger = get_logger()
    log_stage_start(logger, "Saving Bootstrap Results")
    
    if not bootstrap_scores:
        raise ValueError("No bootstrap scores to save.")
    
    scores_array = np.array(bootstrap_scores)
    mean_r2 = float(np.mean(scores_array))
    std_r2 = float(np.std(scores_array))
    
    # Calculate percentile-based confidence interval
    lower_percentile = (1 - confidence_level) / 2
    upper_percentile = 1 - lower_percentile
    ci_lower = float(np.percentile(scores_array, lower_percentile * 100))
    ci_upper = float(np.percentile(scores_array, upper_percentile * 100))
    
    result = {
        "bootstrap_samples": len(bootstrap_scores),
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "confidence_level": confidence_level,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": ci_upper - ci_lower,
        "distribution": {
            "min": float(np.min(scores_array)),
            "max": float(np.max(scores_array)),
            "median": float(np.median(scores_array)),
            "percentiles": {
                "5": float(np.percentile(scores_array, 5)),
                "25": float(np.percentile(scores_array, 25)),
                "75": float(np.percentile(scores_array, 75)),
                "95": float(np.percentile(scores_array, 95))
            }
        }
    }
    
    # Ensure output directory exists
    ensure_dirs()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    log_stage_complete(logger, f"Results saved to {output_path}")
    return result

def main() -> bool:
    """
    Main entry point for T023: Bootstrap resampling of outer-fold predictions.
    
    1. Load predictions from data/processed/predictions.npy
    2. Perform 1000 bootstrap resamples
    3. Calculate 95% CI on R²
    4. Save results to data/results/bootstrap_ci.json
    """
    logger = get_logger()
    log_stage_start(logger, "Evaluation")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    try:
        # Load predictions
        predictions_path = "data/processed/predictions.npy"
        predictions, y_true, subject_ids = load_predictions(predictions_path)
        
        # Validate data
        if len(predictions) != len(y_true):
            raise ValueError("Predictions and true values length mismatch.")
        if len(predictions) == 0:
            raise ValueError("No predictions found in input file.")
        
        logger.log_operation("data_validation", n_samples=len(predictions))
        
        # Perform bootstrap resampling
        bootstrap_scores = bootstrap_resample_r2(
            y_true=y_true,
            y_pred=predictions,
            n_iterations=1000,
            random_state=get_hyperparameter("random_seed", 42)
        )
        
        if not bootstrap_scores:
            raise RuntimeError("Bootstrap resampling was interrupted or produced no results.")
        
        # Save results
        output_path = "data/results/bootstrap_ci.json"
        results = save_bootstrap_results(bootstrap_scores, output_path)
        
        # Log final metrics
        logger.log_operation(
            "bootstrap_complete",
            mean_r2=results["mean_r2"],
            ci_95=[results["ci_lower"], results["ci_upper"]]
        )
        
        print(f"Bootstrap analysis complete. Results saved to {output_path}")
        print(f"Mean R²: {results['mean_r2']:.4f}")
        print(f"95% CI: [{results['ci_lower']:.4f}, {results['ci_upper']:.4f}]")
        
        return True
        
    except Exception as e:
        log_stage_error(logger, str(e))
        print(f"Error during evaluation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)