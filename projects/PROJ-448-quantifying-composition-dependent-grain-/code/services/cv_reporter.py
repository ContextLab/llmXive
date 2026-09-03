import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from code.config import PROCESSED_PATH, get_logger
from code.errors import ValidationError

logger = get_logger(__name__)

def load_cv_results() -> Dict[str, Any]:
    """
    Load cross-validation results from the aggregated JSON file.
    Expects the file to contain a list of fold results with 'r2' and 'mse' keys.
    """
    input_path = PROCESSED_PATH / "cross_validation_results.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Cross-validation results file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        # Handle case where data might be a dict with a 'folds' key
        if isinstance(data, dict) and 'folds' in data:
            data = data['folds']
        else:
            raise ValidationError("Expected cross-validation results to be a list of fold dictionaries.")
    
    return data

def calculate_fold_metrics(folds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure each fold has the required metrics (r2, mse) calculated.
    If missing, this is a placeholder for calculation logic if needed,
    but typically the CV engine (T029) should have populated these.
    """
    metrics = []
    for i, fold in enumerate(folds):
        fold_metrics = {
            "fold_index": i,
            "r2": fold.get("r2", 0.0),
            "mse": fold.get("mse", 0.0),
            "train_size": fold.get("train_size", 0),
            "test_size": fold.get("test_size", 0)
        }
        metrics.append(fold_metrics)
    return metrics

def compute_summary_statistics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate mean and standard deviation for R² and MSE across folds.
    Flags if standard deviation exceeds the threshold (0.05 for R²).
    """
    if not metrics:
        raise ValidationError("No fold metrics provided to summarize.")

    r2_values = [m["r2"] for m in metrics]
    mse_values = [m["mse"] for m in metrics]

    mean_r2 = float(np.mean(r2_values))
    std_r2 = float(np.std(r2_values))
    
    mean_mse = float(np.mean(mse_values))
    std_mse = float(np.std(mse_values))

    # Threshold for stability check
    r2_std_threshold = 0.05
    is_stable = std_r2 <= r2_std_threshold

    summary = {
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "mean_mse": mean_mse,
        "std_mse": std_mse,
        "num_folds": len(metrics),
        "r2_std_threshold": r2_std_threshold,
        "is_stable": is_stable
    }
    
    return summary

def report_metrics(summary: Dict[str, Any]) -> None:
    """
    Log the required output format: "Mean R²: X, Std Dev: Y"
    and flag if Std Dev > 0.05.
    """
    mean_r2 = summary["mean_r2"]
    std_r2 = summary["std_r2"]
    is_stable = summary["is_stable"]

    log_message = f"Mean R²: {mean_r2:.4f}, Std Dev: {std_r2:.4f}"
    logger.info(log_message)

    if not is_stable:
        logger.warning(f"Cross-validation instability detected: Std Dev ({std_r2:.4f}) > Threshold (0.05).")
    else:
        logger.info("Cross-validation stability check passed.")

def save_cv_metrics_report(summary: Dict[str, Any], metrics: List[Dict[str, Any]]) -> Path:
    """
    Save the detailed metrics and summary to data/processed/cv_metrics.json.
    """
    output_path = PROCESSED_PATH / "cv_metrics.json"
    
    report_data = {
        "summary": summary,
        "fold_details": metrics
    }

    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Cross-validation metrics report saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for T030-Exec.
    1. Load CV results.
    2. Calculate per-fold metrics.
    3. Compute summary statistics (Mean/Std Dev).
    4. Log results in required format.
    5. Save report to data/processed/cv_metrics.json.
    """
    try:
        logger.info("Starting Cross-Validation Metrics Reporting (T030)...")
        
        # Load data
        folds = load_cv_results()
        
        # Ensure metrics are present
        fold_metrics = calculate_fold_metrics(folds)
        
        # Compute summary
        summary = compute_summary_statistics(fold_metrics)
        
        # Report to logs
        report_metrics(summary)
        
        # Save artifact
        save_cv_metrics_report(summary, fold_metrics)
        
        logger.info("T030 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T030: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
