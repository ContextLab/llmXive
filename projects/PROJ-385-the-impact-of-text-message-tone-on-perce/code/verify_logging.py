"""
Verification script for logging infrastructure (Task T008).
Runs a dummy pipeline start/stop to ensure data/pipeline.log is created with entries.
"""
import sys
from pathlib import Path

# Ensure we can import from the code directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from logging_config import setup_logging, log_pipeline_step, log_exclusion, get_logger


def main():
    """
    Execute a dummy pipeline sequence to verify logging functionality.
    """
    print("Starting logging verification (Task T008)...")

    # Initialize the logger
    logger = setup_logging()
    logger.info("Logging infrastructure verification started.")

    # Simulate a pipeline step
    log_pipeline_step("Data Loading", "Loading stimuli and ratings from raw directory.")
    log_pipeline_step("Data Cleaning", "Detecting straight-lining and missing data.")

    # Simulate an exclusion event
    log_exclusion("Straight-lining detected", participant_id="P-12345")
    log_exclusion("Missing data", participant_id="P-67890")

    # Simulate completion
    log_pipeline_step("Analysis", "LMM execution completed.")
    logger.info("Logging infrastructure verification completed successfully.")

    print("Verification complete. Check 'data/pipeline.log' for entries.")


if __name__ == "__main__":
    main()