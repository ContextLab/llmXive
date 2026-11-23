import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

METRICS_FILE = Path("data/processed/metric_runs.json")
BEST_PARAMS_FILE = Path("data/processed/best_hyperparameters.json")

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute standard regression metrics: RMSE, R², MAE.
    
    Args:
        y_true: Array of true values (T_d).
        y_pred: Array of predicted values.
        
    Returns:
        Dictionary with keys 'rmse', 'r2', 'mae'.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Mean Squared Error
    mse = np.mean((y_true - y_pred) ** 2)
    rmse = np.sqrt(mse)
    
    # Mean Absolute Error
    mae = np.mean(np.abs(y_true - y_pred))
    
    # R-squared (Coefficient of Determination)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        r2 = 0.0 if ss_res == 0 else -np.inf
    else:
        r2 = 1 - (ss_res / ss_tot)
    
    return {
        "rmse": float(rmse),
        "r2": float(r2),
        "mae": float(mae)
    }

def log_metric_result(
    model_type: str,
    hyperparameters: Dict[str, Any],
    metrics: Dict[str, float],
    fold_idx: Optional[int] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Structure a single metric logging entry.
    
    Args:
        model_type: String identifier (e.g., 'RandomForest').
        hyperparameters: Dict of hyperparameters used.
        metrics: Dict of computed metrics (rmse, r2, mae).
        fold_idx: Optional fold index for CV.
        timestamp: ISO format timestamp.
        
    Returns:
        Dictionary representing the log entry.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
        
    entry = {
        "timestamp": timestamp,
        "model_type": model_type,
        "hyperparameters": hyperparameters,
        "metrics": metrics
    }
    
    if fold_idx is not None:
        entry["fold"] = fold_idx
        
    logger.info(f"Logged metrics for {model_type}: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
    return entry

def track_best_hyperparameters(
    all_runs: List[Dict[str, Any]],
    metric_name: str = "r2"
) -> Dict[str, Any]:
    """
    Identify the best hyperparameter set based on a specific metric.
    
    Args:
        all_runs: List of metric log entries.
        metric_name: Key in metrics dict to maximize (e.g., 'r2') or minimize ('rmse').
        
    Returns:
        Dictionary with best run details.
    """
    if not all_runs:
        return {}
        
    is_maximizing = metric_name == "r2"
    
    best_run = None
    best_score = -np.inf if is_maximizing else np.inf
    
    for run in all_runs:
        score = run["metrics"].get(metric_name)
        if score is None:
            continue
            
        if is_maximizing:
            if score > best_score:
                best_score = score
                best_run = run
        else:
            if score < best_score:
                best_score = score
                best_run = run
                
    if best_run:
        logger.info(f"Best {metric_name} found: {best_score:.4f}")
    return best_run

def save_metric_summary(
    runs: List[Dict[str, Any]],
    best_run: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save all metric runs and the best run to JSON files.
    
    Args:
        runs: List of all metric log entries.
        best_run: The best run entry (optional, if already computed).
    """
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save all runs
    with open(METRICS_FILE, "w") as f:
        json.dump(runs, f, indent=2)
    logger.info(f"Saved {len(runs)} metric runs to {METRICS_FILE}")
    
    # Save best run if provided
    if best_run:
        BEST_PARAMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BEST_PARAMS_FILE, "w") as f:
            json.dump(best_run, f, indent=2)
        logger.info(f"Saved best hyperparameters to {BEST_PARAMS_FILE}")

def main() -> None:
    """
    CLI entry point for metric logging.
    Expects arguments: model_type, r2, rmse, mae, hyperparameters_json.
    This function is primarily called by model_training.py or grid_search.py
    to log results programmatically.
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Log model metrics")
    parser.add_argument("--model_type", type=str, required=True)
    parser.add_argument("--r2", type=float, required=True)
    parser.add_argument("--rmse", type=float, required=True)
    parser.add_argument("--mae", type=float, required=True)
    parser.add_argument("--hyperparameters", type=str, required=True)
    parser.add_argument("--fold", type=int, default=None)
    
    args = parser.parse_args()
    
    metrics = {"r2": args.r2, "rmse": args.rmse, "mae": args.mae}
    hyperparams = json.loads(args.hyperparameters)
    
    entry = log_metric_result(
        model_type=args.model_type,
        hyperparameters=hyperparams,
        metrics=metrics,
        fold_idx=args.fold
    )
    
    # In a real pipeline, we would accumulate runs and save at the end.
    # For CLI usage, we just log to stdout/stderr for verification.
    print(json.dumps(entry, indent=2))

if __name__ == "__main__":
    main()