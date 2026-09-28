"""
Script to execute the motion exclusion pipeline (T014).
Reads the intermediate data from the ingestion pipeline, applies the motion filter,
logs exclusion details, and writes the filtered dataset.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories
from ingestion import apply_motion_exclusion
from utils import get_logger, read_csv, write_csv

def main():
    logger = get_logger("motion_exclusion")
    logger.info("Starting motion exclusion pipeline (T014).")

    # Define paths based on project conventions
    input_path = PROJECT_ROOT / "data" / "processed" / "intermediate_joined.csv"
    output_path = PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"
    log_path = PROJECT_ROOT / "data" / "processed" / "motion_exclusion_log.txt"

    # Ensure directories exist
    ensure_directories([output_path.parent, log_path.parent])

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the ingestion pipeline (T013) to generate intermediate_joined.csv first.")
        sys.exit(1)

    # Load data
    logger.info(f"Loading data from {input_path}")
    df = read_csv(input_path)

    if df.empty:
        logger.warning("Input dataframe is empty. No data to process.")
        # Write empty file to maintain pipeline continuity
        write_csv(df, output_path)
        return

    # Apply motion exclusion (Threshold: Mean_FD > 0.5mm)
    logger.info("Applying motion exclusion filter (Mean_FD > 0.5mm).")
    filtered_df, exclusion_log = apply_motion_exclusion(df, threshold=0.5)

    # Log exclusion details to file
    with open(log_path, 'w') as f:
        f.write("Motion Exclusion Log (T014)\n")
        f.write("=" * 40 + "\n")
        f.write(f"Input Count: {len(df)}\n")
        f.write(f"Excluded Count: {len(df) - len(filtered_df)}\n")
        f.write(f"Output Count: {len(filtered_df)}\n")
        f.write(f"Threshold: Mean_FD > 0.5mm\n")
        f.write("=" * 40 + "\n")
        f.write("\nExcluded Subject IDs:\n")
        if exclusion_log:
            for item in exclusion_log:
                f.write(f"- {item}\n")
        else:
            f.write("None.\n")

    logger.info(f"Exclusion complete. {len(df) - len(filtered_df)} subjects excluded.")
    logger.info(f"Log written to: {log_path}")

    # Write filtered dataset
    write_csv(filtered_df, output_path)
    logger.info(f"Filtered dataset written to: {output_path}")

    logger.info("Motion exclusion pipeline finished successfully.")

if __name__ == "__main__":
    main()
