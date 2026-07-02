"""
Validation target performance check.

Compares hold-out performance against the >= 75% target.
Logs a warning to artifacts/reports/validation.log if the target is not met.
This is a hypothesis check, not a hard halt.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_path
from utils.logging import setup_logger

# Target accuracy/AUC threshold
TARGET_THRESHOLD = 0.75
LOG_FILE_NAME = "validation.log"
METRICS_FILE_NAME = "holdout_metrics.json"

def load_holdout_metrics() -> Optional[Dict[str, Any]]:
    """Load the holdout metrics from the generated JSON file."""
    metrics_path = get_path("artifacts", "reports", METRICS_FILE_NAME)
    if not metrics_path.exists():
        logging.warning(f"Metrics file not found at {metrics_path}. Cannot perform target check.")
        return None

    with open(metrics_path, "r") as f:
        return json.load(f)

def check_target_performance(metrics: Dict[str, Any]) -> bool:
    """
    Check if the hold-out performance meets the target threshold.
    
    Args:
        metrics: Dictionary containing hold-out metrics.
        
    Returns:
        True if target is met, False otherwise.
    """
    # The metrics file typically contains 'accuracy' or 'auc' or 'r2'
    # We look for a primary metric. Based on T034/T033, we expect 'accuracy' or 'auc'.
    # If it's a regression task, 'r2' might be present.
    # We prioritize 'accuracy' or 'auc' for classification (common in disease resistance).
    
    metric_value = None
    metric_name = None

    if "accuracy" in metrics:
        metric_value = metrics["accuracy"]
        metric_name = "accuracy"
    elif "auc" in metrics:
        metric_value = metrics["auc"]
        metric_name = "auc"
    elif "r2" in metrics:
        metric_value = metrics["r2"]
        metric_name = "r2"
    else:
        # Fallback to the first numeric value found if keys differ
        for key, val in metrics.items():
            if isinstance(val, (int, float)):
                metric_value = val
                metric_name = key
                break

    if metric_value is None:
        logging.error("No numeric performance metric found in holdout_metrics.json.")
        return False

    return metric_value >= TARGET_THRESHOLD, metric_name, metric_value

def log_target_check(result: bool, metric_name: str, metric_value: float) -> None:
    """
    Log the result of the target check to artifacts/reports/validation.log.
    
    Args:
        result: Boolean indicating if the target was met.
        metric_name: Name of the metric checked.
        metric_value: The actual value observed.
    """
    log_dir = get_path("artifacts", "reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / LOG_FILE_NAME

    # Configure a specific logger for this task to avoid cluttering the main pipeline logger
    logger = logging.getLogger("validation_target_check")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if result:
        logger.info(f"Target check PASSED: {metric_name} = {metric_value:.4f} >= {TARGET_THRESHOLD}")
    else:
        # Log as WARNING as per requirement, treating it as a hypothesis not met
        logger.warning(
            f"Target check FAILED (Hypothesis): {metric_name} = {metric_value:.4f} < {TARGET_THRESHOLD}. "
            f"Model performance on hold-out set does not meet the >= 75% target."
        )

def run_target_check() -> bool:
    """
    Main entry point to run the target performance check.
    
    Returns:
        True if target met, False otherwise.
    """
    metrics = load_holdout_metrics()
    if metrics is None:
        return False

    success, metric_name, metric_value = check_target_performance(metrics)
    log_target_check(success, metric_name, metric_value)
    return success

def main():
    """CLI entry point."""
    # Setup basic logging for the script itself if not already done
    if not logging.getLogger().handlers:
        setup_logger()

    result = run_target_check()
    if not result:
        # Do not exit with error code, as this is a warning/hypothesis check
        logging.info("Target check completed with warning.")
    else:
        logging.info("Target check completed successfully.")

if __name__ == "__main__":
    main()