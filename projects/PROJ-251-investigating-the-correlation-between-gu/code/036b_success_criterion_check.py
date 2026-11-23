"""
Task T036b: Success Criterion Check (SC-003)

Verifies if the model's cross-validated accuracy meets the SC-003 target of >60%.
Reads model metrics from data/results/model_metrics.json (produced by T036a/T037)
and updates it with the success criterion status.
"""
import os
import sys
import json
import logging
from pathlib import Path
from code.utils.logging_config import get_logger
from code.utils.config import get_logger as get_config_logger

# Constants
SC003_TARGET_ACCURACY = 0.60
METRICS_FILE = Path("data/results/model_metrics.json")
LOG_FILE = Path("data/results/success_criterion_check.log")

def load_model_metrics() -> dict:
    """Load model metrics from the JSON file."""
    if not METRICS_FILE.exists():
        raise FileNotFoundError(f"Model metrics file not found: {METRICS_FILE}. "
                                "Ensure T036a and T037 have completed successfully.")
    
    with open(METRICS_FILE, 'r') as f:
        return json.load(f)

def check_success_criterion(metrics: dict) -> bool:
    """
    Check if the mean accuracy meets the SC-003 target.
    
    Args:
        metrics: Dictionary containing model metrics.
        
    Returns:
        True if mean_accuracy > 0.60, False otherwise.
    """
    mean_accuracy = metrics.get('mean_accuracy')
    
    if mean_accuracy is None:
        raise ValueError("model_metrics.json does not contain 'mean_accuracy'. "
                         "Ensure T036a calculated this metric.")
    
    return mean_accuracy > SC003_TARGET_ACCURACY

def update_metrics_with_criterion(metrics: dict, meets_target: bool) -> dict:
    """Update the metrics dictionary with the success criterion result."""
    metrics['meets_accuracy_target'] = meets_target
    metrics['success_criterion_threshold'] = SC003_TARGET_ACCURACY
    
    # Add a human-readable status
    if meets_target:
        metrics['criterion_status'] = "PASS"
        metrics['message'] = f"Model accuracy ({metrics['mean_accuracy']:.4f}) exceeds target ({SC003_TARGET_ACCURACY})."
    else:
        metrics['criterion_status'] = "FAIL"
        metrics['message'] = f"Model accuracy ({metrics['mean_accuracy']:.4f}) does not meet target ({SC003_TARGET_ACCURACY})."
        
    return metrics

def write_updated_metrics(metrics: dict) -> None:
    """Write the updated metrics back to the JSON file."""
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)

def log_result(meets_target: bool, mean_accuracy: float) -> None:
    """Log the result to a log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, 'w') as f:
        f.write(f"Task T036b: Success Criterion Check (SC-003)\n")
        f.write(f"Target Accuracy: {SC003_TARGET_ACCURACY}\n")
        f.write(f"Mean Accuracy: {mean_accuracy}\n")
        f.write(f"Result: {'PASS' if meets_target else 'FAIL'}\n")
        f.write(f"Status: {'Success' if meets_target else 'Below Target'}\n")

def run_success_criterion_check() -> dict:
    """
    Main function to run the success criterion check.
    
    Returns:
        Dictionary with the check result.
    """
    logger = get_logger("T036b")
    logger.info("Starting Success Criterion Check (SC-003)")
    
    try:
        # Load metrics
        logger.info(f"Loading metrics from {METRICS_FILE}")
        metrics = load_model_metrics()
        
        # Check criterion
        logger.info(f"Checking if mean_accuracy ({metrics.get('mean_accuracy')}) > {SC003_TARGET_ACCURACY}")
        meets_target = check_success_criterion(metrics)
        
        # Update metrics
        updated_metrics = update_metrics_with_criterion(metrics, meets_target)
        
        # Write updated metrics
        logger.info(f"Writing updated metrics to {METRICS_FILE}")
        write_updated_metrics(updated_metrics)
        
        # Log result
        log_result(meets_target, updated_metrics['mean_accuracy'])
        
        logger.info(f"Success Criterion Check completed. Result: {'PASS' if meets_target else 'FAIL'}")
        
        return {
            "status": "completed",
            "meets_target": meets_target,
            "mean_accuracy": updated_metrics['mean_accuracy'],
            "threshold": SC003_TARGET_ACCURACY
        }
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid metrics: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def main():
    """Entry point for the script."""
    try:
        result = run_success_criterion_check()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
