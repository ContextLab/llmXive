"""
Script to verify SC-002 (Statistical Significance) status.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from utils import get_logger

logger = get_logger("check_sc002")
MODEL_DIR = "data/models"
LOG_DIR = "data/logs"

def load_json_file(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_json_file(path: str, data: Dict[str, Any]):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def check_sc002_status():
    """
    Check SC-002 status and log result.
    """
    stat_comparison = load_json_file(os.path.join(MODEL_DIR, "statistical_comparison.json"))
    
    sc002_met = stat_comparison.get("sc002_met", False)
    p_value = stat_comparison.get("p_value", 1.0)
    
    if not sc002_met:
        logger.warning(f"SC-002 failed: Model not statistically distinguishable from null (p={p_value:.4f})")
        status = "FAILED"
    else:
        logger.info(f"SC-002 passed: Model is statistically distinguishable from null (p={p_value:.4f})")
        status = "PASSED"
    
    audit_log = {
        "status": status,
        "p_value": p_value,
        "sc002_met": sc002_met,
        "message": "SC-002 verification complete."
    }
    
    save_json_file(os.path.join(LOG_DIR, "statistical_significance_audit.json"), audit_log)
    return sc002_met

def run_audit():
    """
    Run the SC-002 audit.
    """
    logger.info("Running SC-002 audit...")
    check_sc002_status()
    logger.info("SC-002 audit completed.")

if __name__ == "__main__":
    run_audit()