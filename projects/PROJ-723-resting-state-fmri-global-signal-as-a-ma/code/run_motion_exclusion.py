import os
import sys
import logging
from pathlib import Path

from utils import get_logger, read_csv, write_csv
from ingestion import apply_motion_exclusion, run_motion_exclusion_pipeline

def main():
    logger = get_logger(__name__)
    logger.info("Starting motion exclusion pipeline (T014).")

    input_path = Path("data/processed/joined_data.csv")
    output_path = Path("data/processed/motion_excluded_data.csv")
    log_path = Path("data/processed/motion_exclusion_log.txt")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Reading input data from {input_path}")
    df = read_csv(str(input_path))

    if df.empty:
        logger.warning("Input dataframe is empty. Nothing to process.")
        write_csv(df, str(output_path))
        with open(log_path, "w") as f:
            f.write("No data to process. Input dataframe was empty.\n")
        return

    logger.info(f"Loaded {len(df)} subjects. Applying motion exclusion (Mean_FD > 0.5mm).")

    filtered_df, exclusion_log = run_motion_exclusion_pipeline(df, threshold=0.5)

    write_csv(filtered_df, str(output_path))
    logger.info(f"Filtered dataset written to {output_path}")

    with open(log_path, "w") as f:
        f.write("Motion Exclusion Log (T014)\n")
        f.write("=" * 40 + "\n")
        f.write(f"Threshold: Mean_FD > 0.5mm\n")
        f.write(f"Total subjects before filtering: {len(df)}\n")
        f.write(f"Total subjects after filtering: {len(filtered_df)}\n")
        f.write(f"Subjects excluded: {len(exclusion_log)}\n")
        f.write("-" * 40 + "\n")
        if exclusion_log:
            f.write("Excluded Subject IDs:\n")
            for entry in exclusion_log:
                f.write(f"  - {entry['subject_id']} (Mean_FD: {entry['mean_fd']:.4f})\n")
        else:
            f.write("No subjects excluded.\n")
    logger.info(f"Exclusion log written to {log_path}")

    logger.info("Motion exclusion pipeline completed successfully.")

if __name__ == "__main__":
    main()
