"""
T008b: Execute coordinate transformation validation and generate calibration report.

This script:
1. Loads calibration parameters (extrinsic matrix, rotation, translation) from config or defaults.
2. Uses the CalibrationValidator from code/src/data/calibration.py to perform validation checks.
3. Generates results/calibration_report.json with validation status and metrics.
4. Blocks execution (exits with error) if validation fails or report is missing.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.calibration import (
    ExtrinsicParams,
    CalibrationReport,
    CalibrationValidator,
    create_calibration_validator,
    validate_calibration
)
from utils.config import get_path, get_hyperparameter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Execute calibration validation and generate report."""
    logger.info("Starting calibration validation process...")

    # Determine output path
    results_dir = get_path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "calibration_report.json"

    # Load or create calibration parameters
    # In a real scenario, these would come from a calibration procedure or config file
    # For now, we use the ExtrinsicParams dataclass to define expected parameters
    try:
        # Attempt to load existing calibration if available
        calibration_data_path = get_path("data") / "calibration_params.json"
        if calibration_data_path.exists():
            with open(calibration_data_path, 'r') as f:
                raw_params = json.load(f)
            extrinsic_params = ExtrinsicParams(**raw_params)
            logger.info(f"Loaded calibration parameters from {calibration_data_path}")
        else:
            # Use default/identity parameters if no calibration file exists
            # This represents a "fresh" calibration state
            logger.warning("No calibration parameters found. Using default identity parameters.")
            extrinsic_params = ExtrinsicParams()
    except Exception as e:
        logger.error(f"Failed to load calibration parameters: {e}")
        # Create a failure report and exit
        failure_report = CalibrationReport(
            status="failed",
            error_message=str(e),
            validation_passed=False,
            metrics={}
        )
        with open(report_path, 'w') as f:
            json.dump(asdict(failure_report), f, indent=2)
        sys.exit(1)

    # Create validator
    validator = create_calibration_validator(extrinsic_params)

    # Perform validation
    # The validate_calibration function performs the actual checks
    # It returns a CalibrationReport object
    report = validate_calibration(validator, extrinsic_params)

    # Save report
    with open(report_path, 'w') as f:
        json.dump(asdict(report), f, indent=2)
    logger.info(f"Calibration report saved to {report_path}")

    # Check if validation passed
    if not report.validation_passed:
        logger.error("Calibration validation FAILED. Blocking execution.")
        logger.error(f"Reason: {report.error_message or 'Validation metrics out of bounds'}")
        sys.exit(1)

    logger.info("Calibration validation PASSED. Execution allowed to continue.")
    return 0

if __name__ == "__main__":
    main()
