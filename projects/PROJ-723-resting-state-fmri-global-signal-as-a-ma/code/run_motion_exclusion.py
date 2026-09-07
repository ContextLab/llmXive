"""
Script to run the motion exclusion pipeline.
Filters subjects where per-subject mean FD > 0.5mm and logs exclusion counts.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger, read_csv, write_csv
from ingestion import apply_motion_exclusion, run_motion_exclusion_pipeline

def main():
    logger = get_logger("run_motion_exclusion")
    logger.info("Starting motion exclusion pipeline execution.")

    input_path = Path("data/processed/validated_data.csv")
    output_path = Path("data/processed/cleaned_data.csv")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. "
                     "Please ensure T013 (subject validation) has completed.")
        sys.exit(1)

    # Run the motion exclusion pipeline
    # This function calls apply_motion_exclusion internally and writes the result
    run_motion_exclusion_pipeline(input_path, output_path)

    logger.info(f"Motion exclusion complete. Output written to: {output_path}")

if __name__ == "__main__":
    main()
