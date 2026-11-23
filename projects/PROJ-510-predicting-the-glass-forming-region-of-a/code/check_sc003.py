"""
Script to verify SC-003 (Sensitivity Stability) status.

This script parses the sensitivity analysis results and logs a failure if
the stability margin exceeds the allowed threshold, ensuring the report
explicitly flags unstable thresholds.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Import logger from existing utils module
try:
    from utils import get_logger
except ImportError:
    # Fallback if utils is not in path (e.g., running directly)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
else:
    logger = get_logger("check_sc003")

MODEL_DIR = "data/models"
LOG_DIR = "data/logs"

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file if it exists, otherwise return an empty dict."""
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {path}: {e}")
            return {}
    logger.warning(f"File not found: {path}")
    return {}

def save_json_file(path: str, data: Dict[str, Any]):
    """Save a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def check_sc003_status():
    """
    Check SC-003 status based on sensitivity_status.json.
    
    Reads the stability metrics and logs a failure if the stability margin
    exceeds 5% of the mean (as per SC-003 definition). Writes the audit
    result to sensitivity_stability_audit.json.
    
    Returns:
        bool: True if stability met, False otherwise.
    """
    sensitivity_path = os.path.join(MODEL_DIR, "sensitivity_status.json")
    sensitivity_status = load_json_file(sensitivity_path)
    
    if not sensitivity_status:
        logger.error("sensitivity_status.json is missing or empty. Cannot verify SC-003.")
        # Write a failure audit log to ensure the gate sees the issue
        audit_log = {
            "status": "FAILED",
            "stability_met": False,
            "rmse_variance": None,
            "f1_variance": None,
            "run_status": "FAILED",
            "message": "Source file sensitivity_status.json not found or empty."
        }
        save_json_file(os.path.join(LOG_DIR, "sensitivity_stability_audit.json"), audit_log)
        return False
    
    stability_met = sensitivity_status.get("stability_met", False)
    rmse_variance = sensitivity_status.get("rmse_variance", 0.0)
    f1_variance = sensitivity_status.get("f1_variance", 0.0)
    run_status = sensitivity_status.get("run_status", "UNKNOWN")
    
    if not stability_met:
        logger.warning(f"SC-003 failed: Sensitivity margin exceeds 5% of mean. "
                       f"(RMSE Variance: {rmse_variance:.6f}, F1 Variance: {f1_variance:.6f})")
        status = "FAILED"
    else:
        logger.info(f"SC-003 passed: Sensitivity analysis stable. "
                    f"(RMSE Variance: {rmse_variance:.6f}, F1 Variance: {f1_variance:.6f})")
        status = "PASSED"
    
    audit_log = {
        "status": status,
        "stability_met": stability_met,
        "rmse_variance": rmse_variance,
        "f1_variance": f1_variance,
        "run_status": run_status,
        "message": "SC-003 verification complete."
    }
    
    save_json_file(os.path.join(LOG_DIR, "sensitivity_stability_audit.json"), audit_log)
    return stability_met

def run_audit():
    """
    Run the SC-003 audit and exit with appropriate code.
    
    The script always completes successfully (exit 0) to allow the pipeline
    to continue, but logs warnings and writes the status file as required.
    """
    logger.info("Starting SC-003 Sensitivity Stability Audit...")
    
    try:
        stability_met = check_sc003_status()
        logger.info("SC-003 audit completed.")
        
        # Log the final status clearly
        if not stability_met:
            logger.warning("Pipeline continues with SC-003 failure flag set.")
        else:
            logger.info("SC-003 requirement satisfied.")
            
    except Exception as e:
        logger.error(f"Unexpected error during SC-003 audit: {e}")
        # Ensure we still write a failure log so the gate knows something went wrong
        audit_log = {
            "status": "FAILED",
            "stability_met": False,
            "rmse_variance": None,
            "f1_variance": None,
            "run_status": "ERROR",
            "message": f"Audit execution error: {str(e)}"
        }
        save_json_file(os.path.join(LOG_DIR, "sensitivity_stability_audit.json"), audit_log)
        sys.exit(1)

if __name__ == "__main__":
    run_audit()