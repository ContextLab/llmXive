"""
Verification script for T008: Logging Infrastructure.
Runs a dummy pipeline start/stop to ensure data/pipeline.log is created with entries.
"""
import sys
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logging_config import setup_logging, log_pipeline_step, log_exclusion, get_logger
from config import get_processed_data_dir

def main():
    """
    Executes a dummy pipeline run to verify logging infrastructure.
    """
    print("Starting logging verification (T008)...")

    # 1. Setup logging (this creates the file handler and directory)
    logger = setup_logging()
    logger.info("Logging verification started.")

    # 2. Log a dummy pipeline step
    log_pipeline_step("T008_Dummy_Run", "Verifying log file creation and entry writing.")

    # 3. Log a dummy exclusion (to test exclusion logging)
    log_exclusion("STRAIGHT_LINING_TEST", participant_id="P-VERIFY-001")
    log_exclusion("MISSING_DATA_TEST", participant_id="P-VERIFY-002")

    # 4. Log completion
    log_pipeline_step("T008_Dummy_Run_Completed", "Verification successful.")
    logger.info("Logging verification finished.")

    # 5. Verify file existence
    data_dir = get_processed_data_dir().parent
    log_file = data_dir / "pipeline.log"

    if not log_file.exists():
        print(f"ERROR: Log file {log_file} was not created.")
        sys.exit(1)

    # 6. Verify content
    content = log_file.read_text()
    required_strings = [
        "Pipeline Step: T008_Dummy_Run",
        "Exclusion: STRAIGHT_LINING_TEST",
        "Exclusion: MISSING_DATA_TEST",
        "Pipeline Step: T008_Dummy_Run_Completed"
    ]

    missing = [s for s in required_strings if s not in content]
    if missing:
        print(f"ERROR: Log file missing expected entries: {missing}")
        sys.exit(1)

    print(f"SUCCESS: Log file created at {log_file} with expected entries.")
    print("T008 Verification Passed.")


if __name__ == "__main__":
    main()