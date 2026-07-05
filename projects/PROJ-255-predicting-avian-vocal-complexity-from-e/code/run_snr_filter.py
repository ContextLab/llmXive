"""
T017b: Default Execution of SNR Filtering Engine.

Executes the filtering engine from T017a with the default dB threshold (10 dB)
to generate the primary data/interim/filtered_snr.csv.

Prerequisites:
- data/interim/noise_mapped.csv must exist (output of T015)
- src/data/preprocessing.py must implement filter_by_snr_threshold (T017a)
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocessing import filter_by_snr_threshold
from src.utils.config import get_project_root, get_interim_data_dir
from src.utils.logging import setup_logger

# Configuration
DEFAULT_SNR_THRESHOLD_DB = 10.0
INPUT_FILE_NAME = "noise_mapped.csv"
OUTPUT_FILE_NAME = "filtered_snr.csv"
DROPPED_LOG_NAME = "dropped_snr_records.csv"

def main():
    # Setup logging
    logger = setup_logger("T017b_snr_filter")
    logger.info(f"Starting T017b: SNR Filtering with threshold {DEFAULT_SNR_THRESHOLD_DB} dB")

    project_root = get_project_root()
    interim_dir = get_interim_data_dir()

    # Ensure directories exist
    interim_dir.mkdir(parents=True, exist_ok=True)

    input_path = interim_dir / INPUT_FILE_NAME
    output_path = interim_dir / OUTPUT_FILE_NAME
    dropped_path = interim_dir / DROPPED_LOG_NAME

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Prerequisite T015 (noise_mapped.csv generation) has not been completed.")
        sys.exit(1)

    logger.info(f"Reading input from: {input_path}")

    try:
        filtered_df, dropped_df = filter_by_snr_threshold(
            input_path=str(input_path),
            threshold_db=DEFAULT_SNR_THRESHOLD_DB,
            output_path=str(output_path),
            dropped_log_path=str(dropped_path)
        )

        logger.info(f"Filtering complete.")
        logger.info(f"  - Input records: {len(filtered_df) + len(dropped_df)}")
        logger.info(f"  - Retained records: {len(filtered_df)}")
        logger.info(f"  - Dropped records (SNR <= {DEFAULT_SNR_THRESHOLD_DB}): {len(dropped_df)}")
        logger.info(f"  - Output written to: {output_path}")
        logger.info(f"  - Dropped log written to: {dropped_path}")

    except Exception as e:
        logger.error(f"Error during filtering execution: {e}", exc_info=True)
        sys.exit(1)

    logger.info("T017b execution finished successfully.")

if __name__ == "__main__":
    main()
