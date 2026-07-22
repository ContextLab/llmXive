"""
Script to execute coordinate transformation validation.

This script performs the following steps:
1. Loads extrinsic calibration parameters.
2. Uses the CalibrationValidator to perform coordinate transformation validation.
3. Generates a calibration report in JSON format.
4. Blocks execution (raises error) if validation fails or report is missing.

Output: results/calibration_report.json
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.calibration import (
    ExtrinsicParams,
    CalibrationReport,
    CalibrationValidator,
    create_calibration_validator,
    validate_calibration
)
from src.utils.config import get_path, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for calibration validation.
    
    Executes the validation pipeline and ensures the report is generated.
    If validation fails, raises a RuntimeError to block downstream tasks.
    """
    config = get_config()
    
    # Determine output path
    results_dir = get_path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "calibration_report.json"
    
    logger.info(f"Starting calibration validation. Output: {report_path}")
    
    try:
        # 1. Initialize Validator
        # We assume the validator can be created with default config or from config file
        # If specific calibration data is needed, it should be loaded here.
        # For this implementation, we use the factory function.
        validator = create_calibration_validator()
        
        if validator is None:
            logger.error("Failed to create calibration validator.")
            raise RuntimeError("Calibration validator initialization failed.")
        
        # 2. Perform Validation
        # This function encapsulates the logic to validate coordinate transformations
        # It may load test data or simulate transformations based on the ExtrinsicParams
        report = validate_calibration(validator)
        
        if report is None:
            logger.error("Validation returned no report.")
            raise RuntimeError("Calibration validation produced no report.")
        
        # 3. Check Validation Status
        if not report.is_valid:
            logger.error(f"Calibration validation FAILED. Reason: {report.failure_reason}")
            # Write the failure report before raising to ensure traceability
            with open(report_path, 'w') as f:
                json.dump(report.to_dict(), f, indent=2)
            raise RuntimeError(f"Calibration validation failed: {report.failure_reason}")
        
        logger.info("Calibration validation PASSED.")
        
        # 4. Write Report to Disk
        report_dict = report.to_dict()
        report_dict['status'] = 'success'
        
        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        logger.info(f"Calibration report successfully written to {report_path}")
        
        # 5. Block if missing (Logic handled by the try/except above, 
        # but we explicitly check existence here as a final safeguard)
        if not report_path.exists():
            raise RuntimeError("Critical: Calibration report file missing after successful validation.")
        
        return report

    except Exception as e:
        logger.critical(f"Calibration validation process failed with error: {e}")
        # Ensure we exit with a non-zero code to signal failure to the pipeline
        sys.exit(1)

if __name__ == "__main__":
    main()