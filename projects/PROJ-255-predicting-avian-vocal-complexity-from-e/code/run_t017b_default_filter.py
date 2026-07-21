"""
T017b: Default Execution of SNR Filtering Engine.

Executes the filtering engine from T017a with the default dB threshold
to generate the primary data/interim/filtered_snr.csv.

This script assumes that data/interim/noise_mapped.csv exists (output of T015).
It calls src.data.preprocessing.filter_by_snr_threshold with the default threshold.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running from code/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import filter_by_snr_threshold
from src.utils.config import get_project_root, get_interim_data_dir
from src.utils.logging import setup_logger

# Default SNR threshold as per project specifications
DEFAULT_SNR_THRESHOLD_DB = 10.0

def main():
    """
    Main entry point for T017b.
    Executes the filtering engine with the default threshold.
    """
    # Setup logging
    logger = setup_logger("T017b")
    logger.info("Starting T017b: Default SNR Filter Execution")

    # Get paths
    root = get_project_root()
    interim_dir = get_interim_data_dir()

    input_file = interim_dir / "noise_mapped.csv"
    output_file = interim_dir / "filtered_snr.csv"
    dropped_file = interim_dir / "dropped_snr_records.csv"

    # Verify input exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T015 (noise mapping) has been completed successfully.")
        sys.exit(1)

    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Dropped records file: {dropped_file}")
    logger.info(f"Using default SNR threshold: {DEFAULT_SNR_THRESHOLD_DB} dB")

    try:
        # Execute the filtering engine
        # This function returns a tuple: (filtered_df, dropped_df, summary_dict)
        # or writes directly to files depending on implementation.
        # Based on the API surface, we expect filter_by_snr_threshold to handle the I/O.
        
        result = filter_by_snr_threshold(
            input_path=str(input_file),
            output_path=str(output_file),
            dropped_path=str(dropped_file),
            threshold_db=DEFAULT_SNR_THRESHOLD_DB
        )

        if result:
            filtered_count, dropped_count, total_count = result
            logger.info(f"Filtering complete.")
            logger.info(f"Total records processed: {total_count}")
            logger.info(f"Records retained: {filtered_count}")
            logger.info(f"Records dropped (SNR <= {DEFAULT_SNR_THRESHOLD_DB} dB): {dropped_count}")
            logger.info(f"Output written to: {output_file}")
            logger.info(f"Dropped records log written to: {dropped_file}")
        else:
            # If the function returns None, it likely handled logging internally
            logger.info("Filtering complete. Check logs for details.")

        logger.info("T017b completed successfully.")

    except Exception as e:
        logger.exception(f"Error during filtering execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()