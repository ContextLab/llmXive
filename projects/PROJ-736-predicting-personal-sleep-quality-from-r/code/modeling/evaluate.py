import os
import sys
import json
import signal
import time
import numpy as np
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, log_event, setup_logging
from utils.metrics import pearson_r, r_squared, calculate_metrics

# Global state for graceful shutdown
_shutdown_requested = False
_partial_results = None
_current_handler_registered = False

# Configuration constants (can be overridden via env or config)
MAX_RAM_GB = 6.0
WALL_CLOCK_LIMIT_SECONDS = 3600  # 1 hour default, adjustable
CPU_ONLY = True

def _get_ram_usage_gb() -> float:
    """Get current process RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def _time_limit_handler(signum, frame):
    """Signal handler for wall-clock time limit."""
    global _shutdown_requested
    _shutdown_requested = True
    log_event("TIME_LIMIT_REACHED", "Wall-clock time limit exceeded. Initiating graceful shutdown.")
    # Trigger an exception to break out of loops if possible, or rely on checks
    raise TimeoutError("Wall-clock time limit exceeded")

def _register_time_limit(timeout_seconds: int):
    """Register the signal handler for the time limit."""
    global _current_handler_registered
    if not _current_handler_registered:
        # Only register if running on a platform that supports SIGALRM (Unix)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, _time_limit_handler)
            signal.alarm(timeout_seconds)
            _current_handler_registered = True
            log_event("TIME_LIMIT_REGISTERED", f"Registered time limit of {timeout_seconds} seconds.")
        else:
            log_event("TIME_LIMIT_SKIPPED", "SIGALRM not supported on this platform (e.g., Windows). Time limit enforced via polling only.")

def _ensure_cpu_only():
    """Enforce CPU-only execution by setting environment variables."""
    if CPU_ONLY:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        os.environ["OMP_NUM_THREADS"] = "1"
        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["MKL_NUM_THREADS"] = "1"
        log_event("CPU_ONLY_ENFORCED", "Set environment variables to enforce CPU-only execution.")

def _check_resources():
    """Check RAM usage and raise error if exceeded."""
    current_ram = _get_ram_usage_gb()
    if current_ram > MAX_RAM_GB:
        error_msg = f"RAM usage ({current_ram:.2f} GB) exceeds limit ({MAX_RAM_GB} GB)."
        log_stage_error("RESOURCE_LIMIT_EXCEEDED", error_msg)
        raise MemoryError(error_msg)
    return current_ram

def _flush_partial_results(results: Dict[str, Any], output_path: str):
    """Save partial results to disk before abort."""
    try:
        ensure_dirs(str(Path(output_path).parent))
        results["incomplete"] = True
        results["shutdown_reason"] = "resource_limit"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        log_event("PARTIAL_RESULTS_FLUSHED", f"Partial results saved to {output_path}")
    except Exception as e:
        log_stage_error("FLUSH_FAILED", f"Failed to save partial results: {e}")

def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    model_func: Callable,
    n_permutations: int = 1000,
    subset_size: int = 100,
    output_path: Optional[str] = None,
    time_limit_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run permutation test on a stratified subset.
    Enforces CPU-only, monitors RAM, and respects time limits.
    """
    global _shutdown_requested, _partial_results
    _shutdown_requested = False
    
    # Enforce constraints
    _ensure_cpu_only()
    
    # Register time limit if provided
    if time_limit_seconds:
        _register_time_limit(time_limit_seconds)
    
    # Initialize logging
    logger = setup_logging()
    log_stage_start("PERMUTATION_TEST", f"Starting permutation test with {n_permutations} permutations.")
    
    try:
        # Check RAM before starting
        _check_resources()
        
        # Stratified subset logic (simplified for this task, assumes y is Sleep Score)
        # In a real scenario, use sklearn.model_selection.StratifiedKFold logic if y is categorical,
        # or just random sampling for continuous regression if stratification is by quantile.
        # Here we assume random sampling for continuous target as per typical permutation test on regression.
        if len(y) > subset_size:
            indices = np.random.choice(len(y), subset_size, replace=False)
            X_sub = X[indices]
            y_sub = y[indices]
            log_event("SUBSET_SELECTED", f"Selected {subset_size} subjects for permutation test.")
        else:
            X_sub, y_sub = X, y
            log_event("NO_SUBSET_NEEDED", "Dataset size <= subset_size, using full data.")

        # Baseline score
        baseline_score = model_func(X_sub, y_sub, return_score=True)
        
        null_distribution = []
        start_time = time.time()
        
        for i in range(n_permutations):
            # Check time limit via polling if signal handler didn't trigger
            if time_limit_seconds and (time.time() - start_time) > time_limit_seconds:
                raise TimeoutError("Time limit exceeded during polling check.")
            
            # Check RAM periodically
            if i % 100 == 0:
                _check_resources()
            
            if _shutdown_requested:
                log_event("SHUTDOWN_REQUESTED", "Shutdown requested. Aborting permutation loop.")
                break
            
            # Permute labels
            y_perm = np.random.permutation(y_sub)
            perm_score = model_func(X_sub, y_perm, return_score=True)
            null_distribution.append(perm_score)
            
            # Progress logging
            if (i + 1) % 100 == 0:
                log_event("PERMUTATION_PROGRESS", f"Completed {i+1}/{n_permutations} permutations.")

        null_distribution = np.array(null_distribution)
        
        # Calculate p-value
        # Two-tailed or one-tailed? Typically one-tailed for "is model better than chance?"
        # p = (count(null >= obs) + 1) / (N + 1)
        p_value = (np.sum(null_distribution >= baseline_score) + 1) / (len(null_distribution) + 1)
        
        results = {
            "baseline_score": float(baseline_score),
            "p_value": float(p_value),
            "n_permutations": len(null_distribution),
            "null_distribution_mean": float(np.mean(null_distribution)),
            "null_distribution_std": float(np.std(null_distribution)),
            "subset_size": len(y_sub),
            "incomplete": False
        }
        
        if output_path:
            _flush_partial_results(results, output_path)
        
        log_stage_complete("PERMUTATION_TEST", f"P-value: {p_value:.4f}")
        return results

    except TimeoutError as e:
        log_stage_error("TIMEOUT", str(e))
        if output_path:
            _flush_partial_results({
                "baseline_score": float(baseline_score) if 'baseline_score' in locals() else None,
                "p_value": None,
                "error": str(e)
            }, output_path)
        raise
    except MemoryError as e:
        log_stage_error("MEMORY_LIMIT", str(e))
        raise
    finally:
        if _current_handler_registered:
            signal.alarm(0) # Cancel alarm

def bootstrap_resample_r2(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bootstrap: int = 1000,
    time_limit_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to calculate confidence intervals for R².
    Enforces resource constraints.
    """
    global _shutdown_requested
    _shutdown_requested = False
    
    _ensure_cpu_only()
    if time_limit_seconds:
        _register_time_limit(time_limit_seconds)
    
    log_stage_start("BOOTSTRAP_R2", f"Starting bootstrap resampling with {n_bootstrap} iterations.")
    
    try:
        _check_resources()
        
        r2_scores = []
        start_time = time.time()
        
        for i in range(n_bootstrap):
            if time_limit_seconds and (time.time() - start_time) > time_limit_seconds:
                raise TimeoutError("Time limit exceeded.")
            
            if _shutdown_requested:
                log_event("SHUTDOWN_REQUESTED", "Shutdown requested. Aborting bootstrap.")
                break
            
            # Resample indices with replacement
            indices = np.random.choice(len(y_true), len(y_true), replace=True)
            y_true_boot = y_true[indices]
            y_pred_boot = y_pred[indices]
            
            # Calculate R2
            r2 = r_squared(y_true_boot, y_pred_boot)
            r2_scores.append(r2)
            
            if (i + 1) % 100 == 0:
                log_event("BOOTSTRAP_PROGRESS", f"Completed {i+1}/{n_bootstrap} iterations.")

        r2_scores = np.array(r2_scores)
        ci_lower = np.percentile(r2_scores, 2.5)
        ci_upper = np.percentile(r2_scores, 97.5)
        
        results = {
            "r2_mean": float(np.mean(r2_scores)),
            "r2_std": float(np.std(r2_scores)),
            "ci_95_lower": float(ci_lower),
            "ci_95_upper": float(ci_upper),
            "n_bootstrap": len(r2_scores)
        }
        
        log_stage_complete("BOOTSTRAP_R2", f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        return results

    except (TimeoutError, MemoryError) as e:
        log_stage_error("BOOTSTRAP_FAILED", str(e))
        raise
    finally:
        if _current_handler_registered:
            signal.alarm(0)

def run_sensitivity_analysis(
    X: np.ndarray,
    y: np.ndarray,
    model_func: Callable,
    variance_thresholds: List[float] = [0.01, 0.05, 0.1],
    pca_retentions: List[float] = [0.95, 0.90, 0.85],
    time_limit_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis over variance thresholds and PCA retention.
    Enforces time budget and resource limits.
    """
    global _shutdown_requested
    _shutdown_requested = False
    
    _ensure_cpu_only()
    if time_limit_seconds:
        _register_time_limit(time_limit_seconds)
    
    log_stage_start("SENSITIVITY_ANALYSIS", f"Starting sensitivity analysis. Time limit: {time_limit_seconds}s")
    
    results = []
    start_time = time.time()
    
    try:
        for vt in variance_thresholds:
            if time_limit_seconds and (time.time() - start_time) > time_limit_seconds:
                raise TimeoutError("Time limit exceeded.")
            if _shutdown_requested:
                break
            
            for pca_ret in pca_retentions:
                if time_limit_seconds and (time.time() - start_time) > time_limit_seconds:
                    raise TimeoutError("Time limit exceeded.")
                if _shutdown_requested:
                    break
                
                try:
                    # Check RAM
                    _check_resources()
                    
                    # Run model with these hyperparameters
                    # Assumes model_func accepts kwargs for these settings or they are global/config
                    # For this implementation, we assume model_func handles internal config or we pass them
                    # Since the signature isn't fully defined in the prompt for model_func, we assume it takes X, y
                    # and reads config, or we wrap it.
                    # To be safe, we assume the user passes a function that already incorporates these settings
                    # or we use a wrapper. Here, we assume the function handles the logic or we pass params.
                    # Let's assume we can pass params:
                    score = model_func(X, y, variance_threshold=vt, pca_retention=pca_ret, return_score=True)
                    
                    results.append({
                        "variance_threshold": vt,
                        "pca_retention": pca_ret,
                        "score": float(score)
                    })
                    log_event("SENSITIVITY_ROW", f"vt={vt}, pca={pca_ret}, score={score:.4f}")
                    
                except Exception as e:
                    log_stage_error("SENSITIVITY_ROW_FAILED", f"Failed for vt={vt}, pca={pca_ret}: {e}")
                    results.append({
                        "variance_threshold": vt,
                        "pca_retention": pca_ret,
                        "score": None,
                        "error": str(e)
                    })

        return {
            "sensitivity_analysis": results,
            "incomplete": _shutdown_requested or (time_limit_seconds and (time.time() - start_time) > time_limit_seconds)
        }

    except (TimeoutError, MemoryError) as e:
        log_stage_error("SENSITIVITY_ANALYSIS_FAILED", str(e))
        return {
            "sensitivity_analysis": results,
            "incomplete": True,
            "error": str(e)
        }
    finally:
        if _current_handler_registered:
            signal.alarm(0)

def load_predictions(path: str) -> np.ndarray:
    """Load predictions from .npy file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Predictions file not found: {path}")
    return np.load(path)

def main():
    """
    Main entry point for evaluate.py.
    Demonstrates the resource enforcement and signal handling.
    """
    paths = get_paths()
    ensure_dirs(paths["results"])
    
    # Setup logging
    log_path = paths["logs"] / "evaluate_run.json"
    setup_logging(log_file=log_path)
    
    log_event("EVALUATE_START", "Starting evaluation module resource enforcement test.")
    
    # Example: Run a dummy permutation test if data exists
    # In a real run, this would be called by the pipeline with actual data
    try:
        # Check if we have predictions to bootstrap
        pred_path = paths["processed"] / "predictions.npy"
        if pred_path.exists():
            y_true = np.random.rand(100) # Placeholder for real y
            y_pred = load_predictions(str(pred_path))
            if len(y_pred) != len(y_true):
                y_true = np.random.rand(len(y_pred))
            
            log_event("BOOTSTRAP_START", "Running bootstrap on predictions.")
            bootstrap_results = bootstrap_resample_r2(y_true, y_pred, n_bootstrap=100, time_limit_seconds=60)
            log_event("BOOTSTRAP_COMPLETE", json.dumps(bootstrap_results))
        else:
            log_event("NO_PREDICTIONS", "No predictions found to bootstrap.")
            
        log_event("EVALUATE_COMPLETE", "Evaluation module finished successfully.")
    except Exception as e:
        log_stage_error("EVALUATE_ERROR", str(e))
        raise

if __name__ == "__main__":
    main()