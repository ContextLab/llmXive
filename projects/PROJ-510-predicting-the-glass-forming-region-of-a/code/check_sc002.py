"""
Script to verify SC-002 (Statistical Significance) status.

This script parses the statistical comparison results and logs a WARNING if
the model is not statistically distinguishable from the null model.
It does NOT exit with code 1, ensuring the pipeline continues to generate
the report with this negative finding flagged.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from utils import get_logger

# Configure paths relative to project root
MODEL_DIR = "data/models"
LOG_DIR = "data/logs"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

logger = get_logger("check_sc002")

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
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

def check_sc002_status():
    """
    Check SC-002 status based on statistical_comparison.json.
    
    Reads the p-value and sc002_met flag. If sc002_met is False, logs a WARNING.
    Writes the audit result to data/logs/statistical_significance_audit.json.
    """
    stat_comparison_path = os.path.join(MODEL_DIR, "statistical_comparison.json")
    stat_comparison = load_json_file(stat_comparison_path)
    
    if not stat_comparison:
        logger.error("statistical_comparison.json is missing or empty. Cannot verify SC-002.")
        audit_log = {
            "status": "ERROR",
            "p_value": None,
            "sc002_met": False,
            "message": "statistical_comparison.json missing or invalid."
        }
        save_json_file(os.path.join(LOG_DIR, "statistical_significance_audit.json"), audit_log)
        return False

    sc002_met = stat_comparison.get("sc002_met", False)
    p_value = stat_comparison.get("p_value", 1.0)
    t_statistic = stat_comparison.get("t_statistic", 0.0)
    
    # Log the specific outcome
    if not sc002_met:
        logger.warning(f"SC-002 failed: Model not statistically distinguishable from null (p={p_value:.4f}, t={t_statistic:.4f})")
        status = "FAILED"
    else:
        logger.info(f"SC-002 passed: Model is statistically distinguishable from null (p={p_value:.4f}, t={t_statistic:.4f})")
        status = "PASSED"
    
    audit_log = {
        "status": status,
        "p_value": p_value,
        "t_statistic": t_statistic,
        "sc002_met": sc002_met,
        "message": "SC-002 verification complete."
    }
    
    save_json_file(os.path.join(LOG_DIR, "statistical_significance_audit.json"), audit_log)
    return sc002_met

def run_audit():
    """
    Run the SC-002 audit.
    """
    logger.info("Starting SC-002 audit...")
    check_sc002_status()
    logger.info("SC-002 audit completed.")

if __name__ == "__main__":
    run_audit()