import os
import sys
import logging
from pathlib import Path

from utils import get_logger, read_csv, write_csv
from ingestion import apply_motion_exclusion, run_motion_exclusion_pipeline

def main():
    """
    Main entry point for the motion exclusion runner.
    Reads joined data, applies exclusion, writes filtered data.
    """
    logger = get_logger("run_motion_exclusion")
    logger.info("Starting motion exclusion runner.")

    # Define paths
    input_path = Path("data/processed/joined_data.csv")
    output_path = Path("data/processed/motion_excluded.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Ensure T013 (join_fmri_mwq_data) has been run and produced joined_data.csv")
        sys.exit(1)

    # Load data
    logger.info(f"Loading data from {input_path}")
    df = read_csv(input_path)
    
    if df is None or df.empty:
        logger.error("Loaded dataframe is empty.")
        sys.exit(1)

    # Run exclusion
    logger.info("Applying motion exclusion logic...")
    filtered_df, log_info = apply_motion_exclusion(df, threshold=0.5, logger=logger)

    if filtered_df is not None and not filtered_df.empty:
        # Write output
        logger.info(f"Writing filtered data to {output_path}")
        write_csv(filtered_df, output_path)
        
        # Log summary
        logger.info(f"Exclusion Summary: {log_info['excluded_count']} subjects excluded out of {log_info['total_subjects']}.")
        if log_info['excluded_ids']:
            logger.info(f"Excluded IDs: {log_info['excluded_ids']}")
    else:
        logger.warning("No data remained after motion exclusion.")
    
    logger.info("Motion exclusion runner completed.")

if __name__ == "__main__":
    main()
