"""
Task T004b: Power Logging
Reads power check results from T004a, logs appropriate warnings based on subject count,
and updates the reproducibility report with power warnings.
"""
import os
import json
import logging
from pathlib import Path
import pandas as pd
from utils.logging import setup_logger
from utils.config import get_config

# Setup logger
logger = setup_logger(__name__)

def load_power_check_results(power_check_path: str) -> dict:
    """Load power check results from T004a."""
    if not os.path.exists(power_check_path):
        raise FileNotFoundError(f"Power check results not found at {power_check_path}")
    
    with open(power_check_path, 'r') as f:
        return json.load(f)

def load_reproducibility_report(report_path: str) -> dict:
    """Load existing reproducibility report or create empty structure."""
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            return json.load(f)
    return {"pipeline_metrics": {}}

def save_reproducibility_report(report_path: str, report: dict):
    """Save updated reproducibility report."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

def log_power_warning(n_subjects: int, threshold: int) -> str:
    """
    Log appropriate warning based on subject count.
    Returns the warning message.
    """
    if n_subjects < threshold:
        msg = f"Underpowered for small effects (r=0.3). N={n_subjects} < {threshold}"
        logger.warning(msg)
        return msg
    elif n_subjects < 85:
        msg = f"N < 85: Power may be limited for small effects. N={n_subjects}"
        logger.warning(msg)
        return msg
    else:
        msg = f"Power sufficient. N={n_subjects} >= 85"
        logger.info(msg)
        return msg

def update_reproducibility_report(report: dict, warning_message: str, n_subjects: int, threshold: int) -> dict:
    """
    Update reproducibility report with power warning if N < 50.
    """
    if "pipeline_metrics" not in report:
        report["pipeline_metrics"] = {}
    
    # Log power status
    report["pipeline_metrics"]["power_status"] = {
        "n_subjects": n_subjects,
        "threshold": threshold,
        "warning": warning_message,
        "power_warning": n_subjects < 50
    }
    
    return report

def run_power_logging(power_check_path: str = None, report_path: str = None):
    """
    Main function to run power logging task.
    """
    config = get_config()
    
    # Default paths if not provided
    if power_check_path is None:
        power_check_path = str(config.output_paths.processed_behavioral / "power_metrics.json")
    if report_path is None:
        report_path = str(config.output_paths.processed_behavioral.parent / "reproducibility_report.json")
    
    logger.info(f"Loading power check results from {power_check_path}")
    power_results = load_power_check_results(power_check_path)
    
    n_subjects = power_results.get("n_subjects", 0)
    threshold = power_results.get("threshold", 50)
    
    logger.info(f"Subject count: {n_subjects}, Threshold: {threshold}")
    
    # Log appropriate warning
    warning_message = log_power_warning(n_subjects, threshold)
    
    # Load and update reproducibility report
    logger.info(f"Updating reproducibility report at {report_path}")
    report = load_reproducibility_report(report_path)
    report = update_reproducibility_report(report, warning_message, n_subjects, threshold)
    save_reproducibility_report(report_path, report)
    
    logger.info("Power logging completed successfully")
    
    return {
        "n_subjects": n_subjects,
        "threshold": threshold,
        "warning": warning_message,
        "power_warning": n_subjects < 50
    }

def main():
    """Entry point for the power logging task."""
    try:
        result = run_power_logging()
        logger.info(f"Power logging result: {result}")
    except Exception as e:
        logger.error(f"Power logging failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()