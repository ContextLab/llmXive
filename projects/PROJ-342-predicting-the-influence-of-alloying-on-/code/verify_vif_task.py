"""
Verification script for T083: Statistical Compliance.

This script verifies:
1. data/processed/vif_diagnostic_log.json exists and contains 'flagged_features' (list)
   but does NOT contain a key for 'dropped_features' (or it is empty/absent).
2. artifacts/metrics/sensitivity_analysis.json exists and contains 'r2_variance' (float).
"""
import sys
import json
import logging
from pathlib import Path

from analyze import get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_vif_task() -> bool:
    """
    Verify T083 requirements:
    - VIF log has flagged features, no dropped features.
    - Sensitivity analysis has r2_variance.
    """
    project_root = get_project_root()
    vif_log_path = project_root / "data" / "processed" / "vif_diagnostic_log.json"
    sensitivity_path = project_root / "artifacts" / "metrics" / "sensitivity_analysis.json"

    all_checks_passed = True

    # Check 1: VIF Diagnostic Log
    logger.info(f"Checking VIF diagnostic log at: {vif_log_path}")
    if not vif_log_path.exists():
        logger.error(f"FAIL: {vif_log_path} does not exist.")
        return False

    try:
        with open(vif_log_path, 'r') as f:
            vif_data = json.load(f)
        
        # Verify 'flagged_features' exists and is a list
        if 'flagged_features' not in vif_data:
            logger.error("FAIL: 'flagged_features' key missing in VIF log.")
            all_checks_passed = False
        elif not isinstance(vif_data['flagged_features'], list):
            logger.error("FAIL: 'flagged_features' is not a list.")
            all_checks_passed = False
        else:
            logger.info(f"PASS: 'flagged_features' found: {vif_data['flagged_features']}")

        # Verify NO dropped features (task requires flagging, not dropping)
        # The spec says "flag predictors with VIF > 5 for diagnostic review (do NOT drop)"
        if 'dropped_features' in vif_data:
            if vif_data['dropped_features']:
                logger.error("FAIL: 'dropped_features' is present and non-empty. VIF should only flag, not drop.")
                all_checks_passed = False
            else:
                logger.info("PASS: 'dropped_features' is present but empty (as expected).")
        else:
            logger.info("PASS: 'dropped_features' key is absent (as expected, since we only flag).")

        # Verify 'vif_values' exists for completeness
        if 'vif_values' not in vif_data:
            logger.warning("WARNING: 'vif_values' key missing in VIF log.")
        
    except json.JSONDecodeError as e:
        logger.error(f"FAIL: Invalid JSON in VIF log: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error reading VIF log: {e}")
        return False

    # Check 2: Sensitivity Analysis
    logger.info(f"Checking sensitivity analysis at: {sensitivity_path}")
    if not sensitivity_path.exists():
        logger.error(f"FAIL: {sensitivity_path} does not exist.")
        return False

    try:
        with open(sensitivity_path, 'r') as f:
            sens_data = json.load(f)

        # Verify 'r2_variance' exists and is a float
        if 'r2_variance' not in sens_data:
            logger.error("FAIL: 'r2_variance' key missing in sensitivity analysis.")
            all_checks_passed = False
        elif not isinstance(sens_data['r2_variance'], (int, float)):
            logger.error("FAIL: 'r2_variance' is not a number.")
            all_checks_passed = False
        else:
            logger.info(f"PASS: 'r2_variance' found: {sens_data['r2_variance']}")

        # Verify 'max_depth_sweep' exists for completeness
        if 'max_depth_sweep' not in sens_data:
            logger.warning("WARNING: 'max_depth_sweep' key missing in sensitivity analysis.")
        
    except json.JSONDecodeError as e:
        logger.error(f"FAIL: Invalid JSON in sensitivity analysis: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error reading sensitivity analysis: {e}")
        return False

    if all_checks_passed:
        logger.info("SUCCESS: All T083 statistical compliance checks passed.")
        return True
    else:
        logger.error("FAILURE: Some T083 statistical compliance checks failed.")
        return False

if __name__ == "__main__":
    success = verify_vif_task()
    sys.exit(0 if success else 1)