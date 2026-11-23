import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_config, ensure_directories
from utils.logging import DataPipelineLog

logger = logging.getLogger(__name__)

def _ensure_log_dir() -> Path:
    """Ensure the data/logs directory exists."""
    config = get_config()
    ensure_directories()
    log_dir = Path(config["paths"]["processed_data"]) / ".." / "logs"
    log_dir = log_dir.resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def save_metrics(metrics: Dict[str, Any], filename: str = "metrics.json") -> None:
    """
    Save a dictionary of metrics to a JSON file in data/logs.
    
    This serves as the Single Source of Truth for all model metrics,
    hyperparameters, and validation results to ensure reproducibility.
    
    Args:
        metrics: Dictionary containing metric names and values.
        filename: Name of the output file (default: metrics.json).
    """
    log_dir = _ensure_log_dir()
    output_path = log_dir / filename
    
    # Load existing metrics if file exists to append/update
    existing_metrics = {}
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_metrics = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing metrics file {output_path}: {e}. Starting fresh.")
    
    # Update with new metrics
    # Add timestamp for the current run entry if it's a nested structure
    # or just overwrite the top level if it's a flat metrics dict.
    # To support reproducibility of multiple runs, we append a timestamped entry.
    
    timestamp = datetime.now().isoformat()
    
    # If the incoming metrics looks like a single run result, wrap it
    if "timestamp" not in metrics:
        metrics["timestamp"] = timestamp
    
    # Strategy: If existing is a list, append. If dict, update.
    if isinstance(existing_metrics, list):
        existing_metrics.append(metrics)
    elif isinstance(existing_metrics, dict):
        # If the existing file has a 'runs' key, append there
        if "runs" in existing_metrics:
            existing_metrics["runs"].append(metrics)
        else:
            # Otherwise, assume this is an update to the current state or a new structure
            existing_metrics["latest_run"] = metrics
            existing_metrics["timestamp"] = timestamp
    else:
        existing_metrics = {"runs": [metrics], "timestamp": timestamp}

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(existing_metrics, f, indent=2, default=str)
        logger.info(f"Metrics saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write metrics to {output_path}: {e}")
        raise

def log_model_result(
    model_name: str,
    metrics: Dict[str, float],
    hyperparameters: Dict[str, Any],
    feature_importance: Optional[Dict[str, float]] = None
) -> None:
    """
    Log a complete ModelResult to the central metrics file.
    
    Args:
        model_name: Name of the model (e.g., 'RandomForest', 'XGBoost').
        metrics: Dictionary of evaluation metrics (e.g., {'auc': 0.85, 'f1': 0.82}).
        hyperparameters: Dictionary of model hyperparameters used.
        feature_importance: Optional dictionary of feature names and importance scores.
    """
    entry = {
        "model_name": model_name,
        "metrics": metrics,
        "hyperparameters": hyperparameters,
        "feature_importance": feature_importance,
        "timestamp": datetime.now().isoformat()
    }
    save_metrics(entry, filename="metrics.json")

def log_validation_result(
    test_name: str,
    p_value: float,
    statistic: float,
    significance_threshold: float = 0.05
) -> None:
    """
    Log a statistical test result (e.g., DeLong's test, t-test) to metrics.
    
    Args:
        test_name: Name of the test (e.g., 'DeLong_AUC_Comparison', 'RF_vs_XGB_ttest').
        p_value: The calculated p-value.
        statistic: The test statistic value.
        significance_threshold: Threshold for significance (default 0.05).
    """
    entry = {
        "test_name": test_name,
        "p_value": p_value,
        "statistic": statistic,
        "significant": p_value < significance_threshold,
        "threshold": significance_threshold,
        "timestamp": datetime.now().isoformat()
    }
    save_metrics(entry, filename="metrics.json")

def log_comparison_report(
    best_model: str,
    top_features: List[str],
    genomic_count: int,
    physiological_count: int,
    validation_check: bool
) -> None:
    """
    Log the final comparison report summary to metrics.
    
    Args:
        best_model: Name of the best performing model.
        top_features: List of top feature names.
        genomic_count: Count of genomic markers in top features.
        physiological_count: Count of physiological traits in top features.
        validation_check: Boolean result of the validation gene check (SC-005).
    """
    entry = {
        "report_type": "final_comparison",
        "best_model": best_model,
        "top_features": top_features,
        "feature_breakdown": {
            "genomic": genomic_count,
            "physiological": physiological_count
        },
        "validation_check_passed": validation_check,
        "timestamp": datetime.now().isoformat()
    }
    save_metrics(entry, filename="metrics.json")
