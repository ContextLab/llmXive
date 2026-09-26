"""
Script to validate calibration parameters and generate a calibration report.

This script performs coordinate transformation validation using the calibration
logic from src.data.calibration and generates a JSON report at results/calibration_report.json.
If validation fails, the script exits with a non-zero status to block downstream tasks.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.calibration import create_calibration_validator, validate_calibration
from src.utils.config import get_path, init_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for calibration validation.
    
    1. Initializes configuration
    2. Creates a calibration validator
    3. Runs validation
    4. Generates and saves the calibration report
    5. Exits with error code if validation fails
    """
    logger.info("Starting calibration validation process...")
    
    # Initialize configuration if not already done
    try:
        init_config()
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        sys.exit(1)
    
    # Get output path for the report
    results_dir = get_path("results_dir")
    report_path = results_dir / "calibration_report.json"
    
    # Ensure results directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create calibration validator
    try:
        validator = create_calibration_validator()
    except Exception as e:
        logger.error(f"Failed to create calibration validator: {e}")
        sys.exit(1)
    
    # Run validation
    logger.info("Running calibration validation...")
    try:
        is_valid, report_data = validate_calibration(validator)
    except Exception as e:
        logger.error(f"Calibration validation failed with exception: {e}")
        # Create a failure report
        report_data = {
            "status": "FAILED",
            "error": str(e),
            "is_valid": False,
            "validation_details": {},
            "timestamp": None
        }
        is_valid = False
    
    # Prepare the report
    report = {
        "status": "SUCCESS" if is_valid else "FAILED",
        "is_valid": is_valid,
        "validation_details": report_data.get("validation_details", {}),
        "message": "Calibration validation passed" if is_valid else "Calibration validation failed",
        "report_path": str(report_path)
    }
    
    # Save the report to disk
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Calibration report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Failed to save calibration report: {e}")
        sys.exit(1)
    
    # Block if validation failed
    if not is_valid:
        logger.error("CALIBRATION VALIDATION FAILED - Blocking downstream tasks")
        logger.error(f"Details: {report.get('message')}")
        sys.exit(1)
    
    logger.info("Calibration validation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
