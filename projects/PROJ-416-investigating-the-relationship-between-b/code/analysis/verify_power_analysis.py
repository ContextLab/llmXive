"""
Verification module for Power Analysis artifacts.

This module implements T048:
1. Verifies that `data/metrics/power_analysis.json` exists and contains the `min_N_required` key.
2. Verifies that `reports/results.md` exists and references the `min_N_required` value accurately.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from code.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_power_analysis_json(config: Config) -> Dict[str, Any]:
    """
    Verify the power analysis JSON file exists and has the required schema.
    
    Args:
        config: Project configuration object.
        
    Returns:
        A dictionary with verification results.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        KeyError: If the required key is missing.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    power_file_path = config.POWER_ANALYSIS_PATH
    
    if not os.path.exists(power_file_path):
        raise FileNotFoundError(f"Power analysis file not found: {power_file_path}")
        
    with open(power_file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in power analysis file: {e}", e.doc, e.pos)
    
    required_keys = ['min_N_required', 'effect_size', 'alpha', 'power', 'method']
    missing_keys = [k for k in required_keys if k not in data]
    
    if missing_keys:
        raise KeyError(f"Missing required keys in power analysis JSON: {missing_keys}")
        
    logger.info(f"Power analysis JSON verified. min_N_required = {data['min_N_required']}")
    return data
    
def verify_report_reference(config: Config, power_data: Dict[str, Any]) -> bool:
    """
    Verify that the results report references the min_N_required value.
    
    Args:
        config: Project configuration object.
        power_data: The verified power analysis data dictionary.
        
    Returns:
        True if the reference is found and matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the report file does not exist.
    """
    report_path = config.RESULTS_REPORT_PATH
    
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Results report not found: {report_path}")
        
    with open(report_path, 'r') as f:
        content = f.read()
        
    expected_value = str(power_data['min_N_required'])
    
    # Check if the value is referenced in the text
    # We look for the specific number to ensure accuracy
    if expected_value in content:
        logger.info(f"Report successfully references min_N_required = {expected_value}")
        return True
    else:
        logger.warning(f"Report does NOT reference min_N_required = {expected_value}")
        return False
        
def run_verification(config: Config) -> bool:
    """
    Run the full verification sequence for T048.
    
    Args:
        config: Project configuration object.
        
    Returns:
        True if all verifications pass, False otherwise.
    """
    logger.info("Starting T048 verification: Power Analysis and Report Reference")
    
    try:
        # Step 1: Verify JSON
        power_data = verify_power_analysis_json(config)
        
        # Step 2: Verify Report Reference
        success = verify_report_reference(config, power_data)
        
        if not success:
            logger.error("Verification failed: Report does not reference min_N_required")
            return False
            
        logger.info("T048 Verification PASSED.")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Verification FAILED: {e}")
        return False
    except KeyError as e:
        logger.error(f"Verification FAILED: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Verification FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"Verification FAILED with unexpected error: {e}")
        return False
        
def main():
    """Entry point for the verification script."""
    config = Config()
    success = run_verification(config)
    sys.exit(0 if success else 1)
    
if __name__ == "__main__":
    main()
