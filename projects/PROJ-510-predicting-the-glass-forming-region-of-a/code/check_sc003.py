"""
Script to verify SC-003 (Sensitivity Stability) status.
"""

import os
import sys
import json
import logging
from typing import Dict, Any
from utils import get_logger

logger = get_logger("check_sc003")
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

def check_sc003_status():
    """
    Check SC-003 status and log result.
    """
    sensitivity_status = load_json_file(os.path.join(MODEL_DIR, "sensitivity_status.json"))
    
    stability_met = sensitivity_status.get("stability_met", False)
    rmse_variance = sensitivity_status.get("rmse_variance", 0)
    run_status = sensitivity_status.get("run_status", "UNKNOWN")
    
    if not stability_met:
        logger.warning(f"SC-003 failed: Sensitivity margin exceeds 10% (variance={rmse_variance:.4f})")
        status = "FAILED"
    else:
        logger.info(f"SC-003 passed: Sensitivity analysis stable (variance={rmse_variance:.4f})")
        status = "PASSED"
    
    audit_log = {
        "status": status,
        "stability_met": stability_met,
        "rmse_variance": rmse_variance,
        "run_status": run_status,
        "message": "SC-003 verification complete."
    }
    
    save_json_file(os.path.join(LOG_DIR, "sensitivity_stability_audit.json"), audit_log)
    return stability_met

def run_audit():
    """
    Run the SC-003 audit.
    """
    logger.info("Running SC-003 audit...")
    check_sc003_status()
    logger.info("SC-003 audit completed.")

if __name__ == "__main__":
    run_audit()