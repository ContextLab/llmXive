"""
Preprocessing wrapper script.
Executes the data cleaning and sampling pipeline.
"""
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.clean import run_sampling_pipeline
from utils.config import get_raw_data_dir, get_processed_data_dir, get_state_dir
from utils.logging import initialize_logging

logger = initialize_logging("preprocessing")

def main():
    logger.log("start_preprocessing")
    try:
        # Ensure directories exist
        get_raw_data_dir()
        get_processed_data_dir()
        get_state_dir()

        # Run the sampling pipeline (which includes cleaning/merging)
        run_sampling_pipeline()

        logger.log("end_preprocessing", status="success")
    except Exception as e:
        logger.log("end_preprocessing", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
