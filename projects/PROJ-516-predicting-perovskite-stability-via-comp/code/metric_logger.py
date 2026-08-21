"""
Metric tracking and logging for model training results.

This module implements T023: Track RMSE, R², MAE metrics and log best hyperparameters.
It integrates with the model training pipeline to capture performance metrics
and hyperparameter configurations for all trained models.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Compute standard regression metrics: RMSE, R², and MAE.

    Args:
        y_true: True target values (numpy array)
        y_pred: Predicted target values (numpy array)

    Returns:
        Dictionary with keys 'rmse', 'r2', 'mae' containing float values.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}"
        )

    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty")

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Mean Squared Error
    mse = np.mean((y_true - y_pred) ** 2)
    rmse = np.sqrt(mse)

    # Mean Absolute Error
    mae = np.mean(np.abs(y_true - y_pred))

    # R² (Coefficient of Determination)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        # If all y_true values are identical, R² is undefined (0 by convention)
        r2 = 0.0
    else:
        r2 = 1.0 - (ss_res / ss_tot)

    return {
        "rmse": float(rmse),
        "r2": float(r2),
        "mae": float(mae),
    }


def log_metric_result(
    model_type: str,
    hyperparameters: Dict[str, Any],
    metrics: Dict[str, float],
    cv_folds: Optional[int] = None,
    fold_metrics: Optional[List[Dict[str, float]]] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Log a single model's training results including metrics and hyperparameters.

    Args:
        model_type: Type of model (e.g., 'RandomForest', 'GradientBoosting', 'ElasticNet')
        hyperparameters: Dictionary of hyperparameters used for training
        metrics: Dictionary of computed metrics (rmse, r2, mae)
        cv_folds: Number of cross-validation folds (optional)
        fold_metrics: List of metrics per CV fold (optional)
        output_path: Path to append results to JSON file (optional)

    Returns:
        Dictionary containing the logged result entry.
    """
    timestamp = datetime.now().isoformat()

    result_entry = {
        "timestamp": timestamp,
        "model_type": model_type,
        "hyperparameters": hyperparameters,
        "metrics": metrics,
    }

    if cv_folds is not None:
        result_entry["cv_folds"] = cv_folds

    if fold_metrics is not None:
        result_entry["fold_metrics"] = fold_metrics
        # Compute mean and std across folds
        r2_scores = [f["r2"] for f in fold_metrics if "r2" in f]
        rmse_scores = [f["rmse"] for f in fold_metrics if "rmse" in f]
        mae_scores = [f["mae"] for f in fold_metrics if "mae" in f]

        result_entry["fold_statistics"] = {
            "r2_mean": float(np.mean(r2_scores)) if r2_scores else None,
            "r2_std": float(np.std(r2_scores)) if r2_scores else None,
            "rmse_mean": float(np.mean(rmse_scores)) if rmse_scores else None,
            "rmse_std": float(np.std(rmse_scores)) if rmse_scores else None,
            "mae_mean": float(np.mean(mae_scores)) if mae_scores else None,
            "mae_std": float(np.std(mae_scores)) if mae_scores else None,
        }

    logger.info(
        f"Logged {model_type}: R²={metrics['r2']:.4f}, "
        f"RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}"
    )

    if output_path:
        _append_to_results_file(output_path, result_entry)

    return result_entry


def _append_to_results_file(
    output_path: Path, result_entry: Dict[str, Any]
) -> None:
    """Append a result entry to a JSON file, creating it if it doesn't exist."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        with open(output_path, "r") as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                results = []
    else:
        results = []

    results.append(result_entry)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Appended result to {output_path}")


def track_best_hyperparameters(
    model_type: str,
    hyperparameters: Dict[str, Any],
    metrics: Dict[str, float],
    comparison_metrics: List[Dict[str, Any]],
    metric_name: str = "r2",
    maximize: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Track and identify the best hyperparameters based on a specific metric.

    Args:
        model_type: Type of model being evaluated
        hyperparameters: Current hyperparameters
        metrics: Current metrics
        comparison_metrics: List of all previous results for this model type
        metric_name: Metric to optimize ('r2', 'rmse', 'mae')
        maximize: If True, higher is better (e.g., R²); if False, lower is better (e.g., RMSE)

    Returns:
        Tuple of (best_hyperparameters, best_metrics)
    """
    if metric_name not in ["r2", "rmse", "mae"]:
        raise ValueError(f"Invalid metric_name: {metric_name}")

    current_value = metrics.get(metric_name)
    if current_value is None:
        raise ValueError(f"Metric '{metric_name}' not found in metrics")

    comparison_metrics.append(
        {"hyperparameters": hyperparameters, "metrics": metrics}
    )

    # Find best based on the specified metric
    best_entry = None
    for entry in comparison_metrics:
        val = entry["metrics"].get(metric_name)
        if val is None:
            continue

        if best_entry is None:
            best_entry = entry
            continue

        best_val = best_entry["metrics"].get(metric_name)
        if best_val is None:
            best_entry = entry
            continue

        if maximize:
            if val > best_val:
                best_entry = entry
        else:
            if val < best_val:
                best_entry = entry

    if best_entry is None:
        raise ValueError("No valid entries found for comparison")

    logger.info(
        f"Best {model_type} {metric_name}: {best_entry['metrics'][metric_name]:.4f} "
        f"with params: {best_entry['hyperparameters']}"
    )

    return best_entry["hyperparameters"], best_entry["metrics"]


def save_metric_summary(
    all_results: List[Dict[str, Any]], output_path: Path
) -> None:
    """
    Save a summary of all metric results to a JSON file.

    Args:
        all_results: List of all result entries
        output_path: Path to save the summary
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_models": len(all_results),
        "results": all_results,
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Saved metric summary to {output_path}")


def main() -> None:
    """
    Demonstrate metric tracking functionality with sample data.
    This is a self-test function; real usage is via the imported functions.
    """
    logger.info("Running metric logger self-test...")

    # Sample data for testing
    y_true = np.array([300, 350, 400, 450, 500, 550, 600])
    y_pred = np.array([310, 340, 410, 440, 490, 560, 590])

    # Compute metrics
    metrics = compute_metrics(y_true, y_pred)
    logger.info(f"Computed metrics: {metrics}")

    # Test logging
    test_results = []
    test_results.append(
        log_metric_result(
            model_type="RandomForest",
            hyperparameters={"n_estimators": 100, "max_depth": 10},
            metrics=metrics,
            cv_folds=5,
            fold_metrics=[
                {"r2": 0.85, "rmse": 15.0, "mae": 12.0},
                {"r2": 0.87, "rmse": 14.5, "mae": 11.5},
                {"r2": 0.84, "rmse": 15.5, "mae": 12.5},
                {"r2": 0.86, "rmse": 14.8, "mae": 11.8},
                {"r2": 0.88, "rmse": 14.0, "mae": 11.0},
            ],
        )
    )

    # Test best hyperparameter tracking
    comparison = []
    best_params, best_metrics = track_best_hyperparameters(
        "RandomForest",
        {"n_estimators": 100, "max_depth": 10},
        metrics,
        comparison,
        metric_name="r2",
        maximize=True,
    )

    logger.info(f"Best params: {best_params}")
    logger.info(f"Best metrics: {best_metrics}")

    # Save summary
    test_output = Path("data/processed/metric_test_summary.json")
    save_metric_summary(test_results, test_output)

    logger.info(f"Self-test complete. Results saved to {test_output}")


if __name__ == "__main__":
    main()
