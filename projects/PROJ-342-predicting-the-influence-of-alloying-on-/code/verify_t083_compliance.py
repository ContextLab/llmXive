"""
Task T083: Statistical Compliance Verification.

Verifies:
1. data/processed/vif_diagnostic_log.json exists and contains 'flagged_features' (list) 
   but no 'dropped_features' key (or empty list), satisfying the VIF flagging requirement.
2. artifacts/metrics/sensitivity_analysis.json exists and contains 'r2_variance' (float)
   and 'max_depth_sweep' (list) as required by the sensitivity analysis task.

This script acts as the final verification step for T083.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analyze import get_project_root

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PROJECT_ROOT / 'logs' / 't083_compliance.log')
        ]
    )
    return logging.getLogger(__name__)

def verify_vif_log(logger):
    """
    Verify T035a/b outputs: VIF diagnostic log.
    Requirements:
    - File exists: data/processed/vif_diagnostic_log.json
    - Contains 'flagged_features' (list of strings).
    - Does NOT contain 'dropped_features' or has an empty list (VIF flags, doesn't drop).
    """
    vif_path = PROJECT_ROOT / 'data' / 'processed' / 'vif_diagnostic_log.json'
    
    if not vif_path.exists():
        logger.error(f"FAIL: VIF diagnostic log not found at {vif_path}")
        return False

    try:
        with open(vif_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"FAIL: Invalid JSON in VIF log: {e}")
        return False

    # Check for flagged_features
    if 'flagged_features' not in data:
        logger.error("FAIL: 'flagged_features' key missing from VIF log")
        return False
    
    flagged = data['flagged_features']
    if not isinstance(flagged, list):
        logger.error(f"FAIL: 'flagged_features' is not a list: {type(flagged)}")
        return False

    # Check that no features were dropped (VIF should only flag)
    if 'dropped_features' in data:
        dropped = data['dropped_features']
        if dropped:
            logger.error(f"FAIL: VIF log indicates dropped features: {dropped}. VIF should only flag.")
            return False
    
    logger.info(f"PASS: VIF log valid. Flagged features: {flagged}")
    return True

def verify_sensitivity_analysis(logger):
    """
    Verify T037a/b outputs: Sensitivity analysis results.
    Requirements:
    - File exists: artifacts/metrics/sensitivity_analysis.json
    - Contains 'max_depth_sweep' (list of objects with 'max_depth' and 'r2_score')
    - Contains 'r2_variance' (float)
    """
    sens_path = PROJECT_ROOT / 'artifacts' / 'metrics' / 'sensitivity_analysis.json'

    if not sens_path.exists():
        logger.error(f"FAIL: Sensitivity analysis file not found at {sens_path}")
        return False

    try:
        with open(sens_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"FAIL: Invalid JSON in sensitivity analysis: {e}")
        return False

    # Check for max_depth_sweep
    if 'max_depth_sweep' not in data:
        logger.error("FAIL: 'max_depth_sweep' key missing from sensitivity analysis")
        return False

    sweep = data['max_depth_sweep']
    if not isinstance(sweep, list) or len(sweep) == 0:
        logger.error("FAIL: 'max_depth_sweep' is empty or not a list")
        return False

    # Validate structure of sweep items
    for i, item in enumerate(sweep):
        if 'max_depth' not in item or 'r2_score' not in item:
            logger.error(f"FAIL: Item {i} in 'max_depth_sweep' missing required keys")
            return False

    # Check for r2_variance
    if 'r2_variance' not in data:
        logger.error("FAIL: 'r2_variance' key missing from sensitivity analysis")
        return False

    variance = data['r2_variance']
    if not isinstance(variance, (int, float)):
        logger.error(f"FAIL: 'r2_variance' is not a number: {type(variance)}")
        return False

    logger.info(f"PASS: Sensitivity analysis valid. Variance: {variance}, Sweep points: {len(sweep)}")
    return True

def main():
    logger = setup_logging()
    logger.info("Starting T083 Statistical Compliance Verification...")
    
    vif_ok = verify_vif_log(logger)
    sens_ok = verify_sensitivity_analysis(logger)
    
    if vif_ok and sens_ok:
        logger.info("T083 Compliance Check: SUCCESS")
        return 0
    else:
        logger.error("T083 Compliance Check: FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
