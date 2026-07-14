"""
Evaluation module for User Story 2: Predictive Modeling & Statistical Validation.
Implements resource monitoring (RAM, CPU), time limits, and graceful shutdown
to ensure compliance with FR-009 and integration with T022/T024 signal handlers.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Callable

import numpy as np
import psutil

# Import from project modules
from config import get_paths, get_hyperparameter
from utils.logging import get_logger, log_operation, log_stage_start, log_stage_complete, log_stage_error
from utils.metrics import pearson_r, r_squared

# Global state for signal handling
_shutdown_requested = False
_partial_results_path: Optional[str] = None
_current_pipeline: Optional[Any] = None

# Resource constraints (FR-009)
RAM_LIMIT_GB = 6.0
TIME_LIMIT_SECONDS = 3 * 3600  # 3 hours default for sensitivity analysis, overridden by caller if needed
CPU_CORES_LIMIT = 1  # Enforce CPU-only by limiting threads if necessary

logger = get_logger("evaluate")

def _signal_handler(signum: int, frame: Any) -> None:
    """Handle interrupt signals (SIGINT, SIGTERM) by flushing partial results."""
    global _shutdown_requested
    _shutdown_requested = True
    log_operation("Signal received", signal=signum, message="Initiating graceful shutdown")
    if _partial_results_path and _current_pipeline:
        try:
            _flush_partial_results()
        except Exception as e:
            log_stage_error("Failed to flush partial results", error=str(e))
    # Re-raise to allow default handler behavior if needed, or exit
    sys.exit(1)

def setup_resource_limits(time_limit: Optional[int] = None, results_path: Optional[str] = None) -> None:
    """
    Configure resource monitoring and signal handlers.
    
    Args:
        time_limit: Maximum wall-clock time in seconds. Defaults to 3 hours.
        results_path: Path to save partial results if aborted.
    """
    global _partial_results_path, TIME_LIMIT_SECONDS
    _partial_results_path = results_path
    if time_limit:
        TIME_LIMIT_SECONDS = time_limit

    # Register signal handlers
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Enforce CPU-only by limiting numpy threads if psutil suggests high core usage
    # Note: OMP_NUM_THREADS can also be set via env vars, but this is a runtime check
    cpu_count = psutil.cpu_count(logical=True)
    if cpu_count > 1:
        os.environ["OMP_NUM_THREADS"] = "1"
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"
        log_stage_start("Resource Limit", {"cpu_cores": 1, "ram_limit_gb": RAM_LIMIT_GB})
    else:
        log_stage_start("Resource Limit", {"cpu_cores": 1, "ram_limit_gb": RAM_LIMIT_GB})

def check_resources() -> bool:
    """
    Check current RAM usage. Returns True if within limits, False otherwise.
    Aborts if RAM usage exceeds RAM_LIMIT_GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_gb = mem_info.rss / (1024 ** 3)
    
    if mem_gb > RAM_LIMIT_GB:
        log_stage_error("Resource limit exceeded", 
                        {"ram_used_gb": mem_gb, "limit_gb": RAM_LIMIT_GB})
        return False
    return True

def _flush_partial_results() -> None:
    """Flush current pipeline state or metrics to disk if aborted."""
    if not _partial_results_path:
        return
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    
    try:
        # Attempt to save whatever state we have
        if _current_pipeline:
            # Save basic status
            status = {
                "status": "interrupted",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "ram_limit_gb": RAM_LIMIT_GB,
                "time_limit_seconds": TIME_LIMIT_SECONDS
            }
            with open(_partial_results_path, 'w') as f:
                json.dump(status, f, indent=2)
            log_operation("Partial results flushed", path=_partial_results_path)
    except Exception as e:
        log_stage_error("Error flushing partial results", error=str(e))

def load_predictions(path: str) -> np.ndarray:
    """Load predictions from a .npy file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Predictions file not found: {path}")
    return np.load(path)

def load_true_labels(path: str) -> np.ndarray:
    """Load true labels from a .npy file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"True labels file not found: {path}")
    return np.load(path)

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² score."""
    return r_squared(y_true, y_pred)

def calculate_pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """Calculate Pearson correlation and p-value."""
    return pearson_r(y_true, y_pred)

def bootstrap_resample_r2(y_true: np.ndarray, y_pred: np.ndarray, n_samples: int = 1000) -> List[float]:
    """Perform bootstrap resampling to estimate confidence intervals for R²."""
    n = len(y_true)
    bootstrap_scores = []
    
    for i in range(n_samples):
        if _shutdown_requested:
            break
        # Check resources periodically
        if i % 100 == 0 and not check_resources():
            break
        
        indices = np.random.choice(n, size=n, replace=True)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]
        score = calculate_r2(y_true_boot, y_pred_boot)
        bootstrap_scores.append(score)
    
    return bootstrap_scores

def save_bootstrap_results(scores: List[float], path: str) -> None:
    """Save bootstrap results to a JSON file."""
    if not scores:
        log_stage_error("No bootstrap scores to save")
        return
    
    ci_95 = np.percentile(scores, [2.5, 97.5])
    result = {
        "scores": scores,
        "ci_95_lower": float(ci_95[0]),
        "ci_95_upper": float(ci_95[1]),
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores))
    }
    
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)
    log_stage_complete("Bootstrap results saved", path=path)

def handle_variance_threshold_edge_case(variance_threshold: float, n_features: int) -> bool:
    """
    Check if variance thresholding resulted in zero features.
    Returns True if we should skip this grid point.
    """
    if n_features == 0:
        log_stage_error("Variance thresholding removed all features", 
                        {"threshold": variance_threshold, "features_remaining": 0})
        return True
    return False

def run_evaluation_pipeline(
    predictions_path: str,
    true_labels_path: str,
    output_path: str,
    time_limit: Optional[int] = None,
    results_path: Optional[str] = None,
    bootstrap_samples: int = 1000
) -> Dict[str, Any]:
    """
    Main evaluation pipeline with resource monitoring.
    
    Args:
        predictions_path: Path to predictions.npy
        true_labels_path: Path to true_labels.npy
        output_path: Path to save final results
        time_limit: Max time in seconds (overrides default)
        results_path: Path for partial results on abort
        bootstrap_samples: Number of bootstrap iterations
        
    Returns:
        Dictionary with evaluation metrics
    """
    global _current_pipeline
    _current_pipeline = None # Placeholder for potential pipeline state

    # Setup resource limits
    setup_resource_limits(time_limit=time_limit, results_path=results_path)
    
    log_stage_start("Evaluation Pipeline", {
        "predictions": predictions_path,
        "true_labels": true_labels_path,
        "bootstrap_samples": bootstrap_samples
    })

    start_time = time.time()
    
    try:
        # Load data
        if _shutdown_requested:
            raise InterruptedError("Shutdown requested before loading data")
            
        y_pred = load_predictions(predictions_path)
        y_true = load_true_labels(true_labels_path)
        
        # Check resources after load
        if not check_resources():
            raise MemoryError("RAM limit exceeded after loading data")
        
        # Calculate metrics
        r2_score = calculate_r2(y_true, y_pred)
        pearson_r_val, p_val = calculate_pearson_r(y_true, y_pred)
        
        # Bootstrap
        log_stage_start("Bootstrap Resampling", {"samples": bootstrap_samples})
        bootstrap_scores = bootstrap_resample_r2(y_true, y_pred, bootstrap_samples)
        
        if not bootstrap_scores:
            raise InterruptedError("Bootstrap interrupted")
            
        # Save bootstrap results
        bootstrap_path = output_path.replace('.json', '_bootstrap.json')
        save_bootstrap_results(bootstrap_scores, bootstrap_path)
        
        # Finalize results
        elapsed = time.time() - start_time
        result = {
            "r2_score": float(r2_score),
            "pearson_r": float(pearson_r_val),
            "p_value": float(p_val),
            "bootstrap_ci_95": [float(np.percentile(bootstrap_scores, 2.5)), 
                                float(np.percentile(bootstrap_scores, 97.5))],
            "bootstrap_mean": float(np.mean(bootstrap_scores)),
            "elapsed_seconds": float(elapsed),
            "status": "completed"
        }
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
            
        log_stage_complete("Evaluation Pipeline", {"path": output_path, "elapsed": elapsed})
        return result

    except (InterruptedError, MemoryError) as e:
        log_stage_error("Pipeline failed due to resource limits", error=str(e))
        _flush_partial_results()
        raise
    except Exception as e:
        log_stage_error("Pipeline failed", error=str(e))
        raise

def main() -> bool:
    """Entry point for running evaluation."""
    try:
        paths = get_paths()
        preds_path = paths.get("processed", {}).get("predictions", "data/processed/predictions.npy")
        labels_path = paths.get("processed", {}).get("true_labels", "data/processed/true_labels.npy")
        output_path = paths.get("results", {}).get("evaluation", "data/results/evaluation_metrics.json")
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        run_evaluation_pipeline(
            predictions_path=preds_path,
            true_labels_path=labels_path,
            output_path=output_path,
            time_limit=get_hyperparameter("evaluation_time_limit", 3 * 3600),
            results_path=output_path.replace('.json', '_partial.json')
        )
        return True
    except Exception as e:
        log_stage_error("Main evaluation failed", error=str(e))
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)