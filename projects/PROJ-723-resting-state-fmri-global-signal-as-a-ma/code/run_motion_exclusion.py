"""
Script to execute motion exclusion (T014) on processed data.

This script reads the intermediate data (after T013 validation),
applies the motion filter (Mean_FD > 0.5mm), logs the counts,
and writes the filtered dataset to data/processed/cleaned_data.csv
(or a temporary file if the final pipeline isn't ready).

Usage:
    python code/run_motion_exclusion.py
"""
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import get_logger, read_csv, write_csv
from ingestion import apply_motion_exclusion, run_motion_exclusion_pipeline

def main():
    logger = get_logger(__name__)
    logger.info("Starting Motion Exclusion Pipeline (T014)...")

    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    input_file = data_dir / "validated_data.csv"
    output_file = data_dir / "cleaned_data.csv"

    # Ensure output directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run previous tasks (T013) to generate validated_data.csv first.")
        sys.exit(1)

    logger.info(f"Reading input data from {input_file}")
    try:
        data = read_csv(input_file)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        sys.exit(1)

    if not data:
        logger.warning("Input data is empty. No subjects to process.")
        return

    logger.info(f"Loaded {len(data)} subjects from {input_file}")

    # Run motion exclusion
    filtered_data = run_motion_exclusion_pipeline(data, output_path=output_file)

    logger.info(f"Motion exclusion complete. {len(filtered_data)} subjects retained.")
    logger.info(f"Output saved to {output_file}")

    # Summary
    if len(filtered_data) == 0:
        logger.warning("All subjects were excluded due to motion!")
    else:
        logger.info("Successfully processed motion exclusion.")

if __name__ == "__main__":
    main()