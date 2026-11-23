import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from code.config import Config

logger = logging.getLogger(__name__)
config = Config()

def verify_power_analysis_json(json_path: Optional[str] = None) -> bool:
    """
    Verify that power_analysis.json exists and has required fields.
    
    Args:
        json_path: Optional path to the JSON file. Uses config default if not provided.
        
    Returns:
        True if verification passes, False otherwise.
    """
    path = Path(json_path) if json_path else Path(config.POWER_ANALYSIS_PATH)
    
    if not path.exists():
        logger.error(f"Power analysis file not found: {path}")
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in power analysis file: {e}")
        return False
    
    required_fields = ['min_N_required', 'effect_size', 'alpha', 'power', 'method', 'status']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.error(f"Power analysis JSON missing required fields: {missing_fields}")
        return False
    
    # Validate min_N_required is an integer
    if not isinstance(data['min_N_required'], int):
        logger.error(f"min_N_required must be an integer, got {type(data['min_N_required'])}")
        return False
    
    logger.info(f"Power analysis verification passed: {path}")
    return True

def verify_report_reference(report_path: Optional[str] = None) -> bool:
    """
    Verify that the report references the power analysis correctly.
    
    Args:
        report_path: Optional path to the report file. Uses config default if not provided.
        
    Returns:
        True if verification passes, False otherwise.
    """
    path = Path(report_path) if report_path else Path(config.REPORTS_RESULTS_PATH)
    
    if not path.exists():
        logger.error(f"Report file not found: {path}")
        return False
    
    try:
        with open(path, 'r') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read report file: {e}")
        return False
    
    # Check for power analysis reference
    if 'Minimum N Required' not in content and 'min_N_required' not in content:
        logger.error("Report does not reference minimum N required from power analysis")
        return False
    
    logger.info(f"Report reference verification passed: {path}")
    return True

def run_verification() -> None:
    """Run all power analysis verifications."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify power analysis")
    parser.add_argument("--effect-size", type=float, default=0.15, help="Effect size")
    parser.add_argument("--alpha", type=float, default=0.05, help="Alpha level")
    parser.add_argument("--power", type=float, default=0.8, help="Target power")
    
    args = parser.parse_args()
    
    logger.info("Starting T048 verification: Power Analysis and Report Reference")
    
    json_ok = verify_power_analysis_json()
    report_ok = verify_report_reference()
    
    if json_ok and report_ok:
        logger.info("Verification PASSED")
        sys.exit(0)
    else:
        logger.error("Verification FAILED")
        sys.exit(1)

def main() -> None:
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_verification()