"""
Preprocessing Wrapper Script for Ambient Temperature Influence on Moral Decision Speed.

This script orchestrates the data ingestion pipeline to produce the cleaned dataset
required for downstream modeling and robustness analysis. It satisfies the quickstart
run-book command: python code/preprocessing.py.

Dependencies:
    - T017: code/ingestion.py (Load, Filter & Count, Geospatial Matching, Interpolation)
    - T019c: code/interpolation.py (Gap Interpolation - integrated into ingestion.py logic)

Workflow:
    1. Loads raw Moral Machine data from data/raw/moral_machine.csv.gz.
    2. Fetches/validates ERA5 temperature data (assuming T002d/T002e completed).
    3. Performs geospatial matching and temporal interpolation.
    4. Applies hard filters (location, response time, temperature range).
    5. Outputs the merged, cleaned dataset to data/processed/merged_dataset.parquet.
    6. Updates state checksums.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ingestion import main as ingestion_main
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override
from compute_checksum import main as compute_checksum_main

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the full preprocessing pipeline for moral decision speed analysis."
    )
    parser.add_argument(
        "--input-moral",
        type=str,
        default=str(project_root / "data" / "raw" / "moral_machine.csv.gz"),
        help="Path to the raw Moral Machine dataset.",
    )
    parser.add_argument(
        "--input-era5",
        type=str,
        default=str(project_root / "data" / "raw" / "era5_full.parquet"),
        help="Path to the raw ERA5 temperature dataset.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(project_root / "data" / "processed" / "merged_dataset.parquet"),
        help="Path for the output merged dataset.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=str(project_root / "results" / "logs" / "preprocessing_run.log"),
        help="Path to the log file for this run.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(
        log_file=args.log_file,
        logger_name="preprocessing_pipeline"
    )
    logger.info("Starting preprocessing pipeline.")
    logger.info(f"Input Moral Machine: {args.input_moral}")
    logger.info(f"Input ERA5: {args.input-era5}")
    logger.info(f"Output Path: {args.output}")

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate input existence before running ingestion
    if not os.path.exists(args.input_moral):
        logger.error(f"Input Moral Machine file not found: {args.input_moral}")
        sys.exit(1)
    
    if not os.path.exists(args.input_era5):
        logger.error(f"Input ERA5 file not found: {args.input_era5}. "
                     "Ensure T002d (Stream & Save ERA5 Chunks) has completed successfully.")
        sys.exit(1)

    try:
        # Execute the core ingestion logic
        # The ingestion module is designed to be called via its main() function
        # which handles argument parsing internally or uses defaults. 
        # We override defaults by setting environment variables or passing args if the 
        # ingestion module supports it. For robustness, we call ingestion_main directly
        # and let it handle its own internal logic, assuming it reads from the 
        # standard paths defined in config.py or command line args if we pass them.
        
        # Since ingestion.py expects specific args, we simulate the command line call
        # by constructing an argv list for ingestion_main if it accepts it, 
        # or we rely on ingestion_main to read from the standard paths.
        # Given the task description, ingestion.py is the primary producer.
        
        # To ensure we use the specific input/output paths provided by this wrapper:
        # We will patch sys.argv for the ingestion call or rely on ingestion_main
        # to read from the config if no args are passed. 
        # However, ingestion.py's main() likely parses sys.argv. 
        # We will construct a targeted call.
        
        # Re-creating the argument list for ingestion_main to match its expected signature
        ingestion_args = [
            "ingestion.py",
            "--input", args.input_moral,
            "--temp", args.input_era5, # ingestion.py uses --temp for ERA5 path
            "--output", args.output
        ]
        
        # Save original sys.argv
        original_argv = sys.argv
        
        try:
            # Inject arguments for ingestion
            sys.argv = ingestion_args
            logger.info("Executing ingestion module...")
            ingestion_main()
            logger.info("Ingestion module completed successfully.")
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

        # Verify output was created
        if not output_path.exists():
            logger.error("Ingestion completed but output file was not created.")
            sys.exit(1)
        
        if output_path.stat().st_size == 0:
            logger.error("Ingestion completed but output file is empty.")
            sys.exit(1)

        logger.info(f"Successfully produced: {args.output}")

        # Compute checksum for the new artifact
        logger.info("Computing checksum for merged dataset...")
        checksum_argv = ["compute_checksum.py", "--input", str(output_path)]
        original_argv = sys.argv
        try:
            sys.argv = checksum_argv
            compute_checksum_main()
        finally:
            sys.argv = original_argv
        
        logger.info("Preprocessing pipeline finished successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()