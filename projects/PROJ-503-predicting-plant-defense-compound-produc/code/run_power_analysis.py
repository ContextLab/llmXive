"""
Power Analysis Execution Script for T015.

This script executes the power analysis utility (T009) to determine the required
sample size (n) for detecting a correlation of r=0.5 with alpha=0.05 and power=0.8.
It logs the result to logs/power_analysis.json.

CRITICAL: If the calculated n < 28, it raises E-POWER to abort the pipeline,
as per Plan T009/T015 and FR-009.
"""
import json
import logging
import sys
from pathlib import Path

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.power_analysis import calculate_required_n, run_power_analysis
from code.exceptions import E_POWER
from code.error_handler import raise_power_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TARGET_CORRELATION = 0.5
ALPHA = 0.05
POWER = 0.8
MIN_SAMPLE_SIZE_THRESHOLD = 28
LOG_OUTPUT_PATH = project_root / "logs" / "power_analysis.json"

def main():
    logger.info("Starting Power Analysis (Task T015)...")
    
    # Ensure logs directory exists
    LOG_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Calculate required sample size for the specified parameters
        required_n = calculate_required_n(
            effect_size=TARGET_CORRELATION,
            alpha=ALPHA,
            power=POWER
        )
        
        logger.info(f"Calculated required sample size (n) for r={TARGET_CORRELATION}: {required_n}")

        # Prepare result dictionary
        result = {
            "task_id": "T015",
            "parameters": {
                "effect_size_r": TARGET_CORRELATION,
                "alpha": ALPHA,
                "power": POWER
            },
            "required_sample_size_n": required_n,
            "threshold_check": {
                "min_required": MIN_SAMPLE_SIZE_THRESHOLD,
                "passed": required_n >= MIN_SAMPLE_SIZE_THRESHOLD
            },
            "status": "ABORT" if required_n < MIN_SAMPLE_SIZE_THRESHOLD else "PROCEED"
        }

        # Write results to log file
        with open(LOG_OUTPUT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Power analysis results written to {LOG_OUTPUT_PATH}")

        # CRITICAL CHECK: Abort if n < 28
        if required_n < MIN_SAMPLE_SIZE_THRESHOLD:
            error_msg = (
                f"Power analysis failed: Required sample size (n={required_n}) "
                f"is below the minimum threshold (n={MIN_SAMPLE_SIZE_THRESHOLD}). "
                f"Aborting pipeline per Plan T009/T015 and FR-009."
            )
            logger.error(error_msg)
            # Raise E-POWER to halt execution
            raise_power_error(error_msg)
        
        logger.info("Power analysis passed. Pipeline can proceed to T016.")

    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        # Re-raise to ensure the process exits with non-zero status if it's a power error
        if isinstance(e, E_POWER):
            raise
        raise

if __name__ == "__main__":
    main()
