import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Constants for file paths relative to project root
BKT_PARAMS_PATH = "code/simulate/bkt_params.yaml"
CALIBRATION_REPORT_PATH = "data/pilot/calibration_report.json"
CALIBRATION_METRICS_PATH = "data/pilot/calibration_metrics.json"

def load_yaml_params(path: str) -> Optional[Dict[str, Any]]:
    """
    Load BKT parameters from a YAML file.
    Returns None if the file does not exist or cannot be parsed.
    """
    try:
        import yaml
        if not os.path.exists(path):
            logger.warning(f"BKT parameters file not found: {path}")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.error("PyYAML is required but not installed. Install via: pip install pyyaml")
        return None
    except Exception as e:
        logger.error(f"Failed to load BKT parameters from {path}: {e}")
        return None

def load_json_report(path: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON report file.
    Returns None if the file does not exist or cannot be parsed.
    """
    try:
        if not os.path.exists(path):
            logger.warning(f"Report file not found: {path}")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load report from {path}: {e}")
        return None

def check_calibration_valid() -> bool:
    """
    Enforce that simulation cannot proceed without valid calibration parameters.
    
    Validation logic:
    1. Verify bkt_params.yaml exists and is valid.
    2. Verify calibration_report.json exists and indicates success.
    3. Verify calibration_metrics.json exists and meets thresholds (RMSE diff <= 0.02, abs RMSE <= 0.15).
    
    Returns:
        bool: True if calibration is valid, False otherwise.
    """
    logger.info("Checking calibration validity for simulation pipeline...")
    
    # 1. Check BKT Parameters
    params = load_yaml_params(BKT_PARAMS_PATH)
    if params is None:
        logger.error("Calibration invalid: BKT parameters file missing or invalid.")
        return False
    
    # Ensure required keys exist (basic sanity check)
    required_keys = ['p_learn', 'p_guess', 'p_slip', 'p_init']
    for key in required_keys:
        if key not in params:
            logger.error(f"Calibration invalid: Missing required parameter '{key}' in BKT params.")
            return False
    
    # 2. Check Calibration Report
    report = load_json_report(CALIBRATION_REPORT_PATH)
    if report is None:
        logger.error("Calibration invalid: Calibration report missing.")
        return False
    
    # If the report indicates a failure status, block simulation
    if report.get('status') == 'failed':
        logger.error("Calibration invalid: Calibration report indicates failure.")
        return False

    # 3. Check Calibration Metrics
    metrics = load_json_report(CALIBRATION_METRICS_PATH)
    if metrics is None:
        logger.error("Calibration invalid: Calibration metrics missing.")
        return False
    
    # Validate thresholds from T032
    rmse_diff = metrics.get('rmse_difference')
    abs_rmse = metrics.get('absolute_rmse')
    
    if rmse_diff is None or abs_rmse is None:
        logger.error("Calibration invalid: Metrics missing required fields (rmse_difference, absolute_rmse).")
        return False
    
    # T032 Requirement: Exit code 1 if RMSE difference > 0.02 or absolute RMSE > 0.15
    # T033b Requirement: Enforce simulation cannot proceed without valid calibration.
    if rmse_diff > 0.02:
        logger.error(f"Calibration invalid: RMSE difference ({rmse_diff}) exceeds threshold (0.02).")
        return False
    
    if abs_rmse > 0.15:
        logger.error(f"Calibration invalid: Absolute RMSE ({abs_rmse}) exceeds threshold (0.15).")
        return False
    
    logger.info("Calibration validation PASSED. Simulation can proceed.")
    return True

def main() -> int:
    """
    Entry point for the calibration validation script.
    Returns 0 if calibration is valid, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Check if calibration parameters are valid for simulation."
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Path to write a JSON status file (optional)."
    )
    args = parser.parse_args()
    
    is_valid = check_calibration_valid()
    
    if args.output_json:
        try:
            status = {"calibration_valid": is_valid}
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
            logger.info(f"Status written to {args.output_json}")
        except Exception as e:
            logger.error(f"Failed to write output JSON: {e}")
            return 1
    
    if is_valid:
        logger.info("Validation successful. Returning exit code 0.")
        return 0
    else:
        logger.error("Validation failed. Returning exit code 1.")
        return 1

if __name__ == "__main__":
    sys.exit(main())