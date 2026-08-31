"""
Main entry point for the Statistical Discrepancies Pipeline.

Orchestrates data ingestion, discrepancy calculation, and artifact persistence.
Ensures raw data is saved to data/raw/ with checksums and processed data to data/processed/.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).resolve().parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from logger import setup_logging, get_logger
from ingestion import DataIngestionPipeline
from discrepancy import DiscrepancyCalculator
from utils.hashing import save_checksums, compute_file_hash
from models import validate_output_schema
from exceptions import DataAcquisitionError, ConfigurationError
from setup_data_directories import setup_data_directories

logger = get_logger(__name__)

def ensure_directories(project_root: Path) -> None:
    """Ensure required data directories exist."""
    setup_data_directories(project_root)
    logger.info(f"Verified directory structure at {project_root}")

def main():
    parser = argparse.ArgumentParser(description="Run Statistical Discrepancies Pipeline")
    parser.add_argument(
        "--project-root",
        type=str,
        default="projects/PROJ-064-statistical-discrepancies-in-publicly-av",
        help="Root directory of the project"
    )
    parser.add_argument(
        "--source-urls",
        type=str,
        nargs="+",
        default=[],
        help="URLs to source data (OpenElections/State CSVs). If empty, uses default config."
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="csv",
        choices=["csv", "parquet"],
        help="Output format for processed data"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify checksums of existing data before running"
    )
    args = parser.parse_args()

    # Setup logging
    project_root = Path(args.project_root).resolve()
    setup_logging(project_root / "logs" / "pipeline.log")
    logger.info(f"Starting pipeline execution at {project_root}")

    # 1. Ensure directory structure
    try:
        ensure_directories(project_root)
    except Exception as e:
        logger.critical(f"Failed to setup directories: {e}")
        raise

    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    state_dir = project_root / "state"

    # 2. Ingest Data
    logger.info("Initializing DataIngestionPipeline...")
    ingestion_pipeline = DataIngestionPipeline(
        source_urls=args.source_urls,
        raw_dir=raw_dir,
        logger=logger
    )

    try:
        raw_data_path = ingestion_pipeline.run()
    except DataAcquisitionError as e:
        logger.critical(f"Data acquisition failed: {e}")
        raise
    
    if raw_data_path:
        logger.info(f"Raw data ingested to: {raw_data_path}")
        
        # Compute and save checksum for raw data
        try:
            raw_hash = compute_file_hash(raw_data_path)
            checksum_file = state_dir / "raw_data_checksum.json"
            save_checksums({raw_data_path.name: raw_hash}, checksum_file)
            logger.info(f"Saved checksum for {raw_data_path.name} to {checksum_file}")
        except Exception as e:
            logger.error(f"Failed to compute/save checksum for raw data: {e}")
            raise ConfigurationError(f"Checksum failure: {e}")

    # 3. Calculate Discrepancies
    logger.info("Initializing DiscrepancyCalculator...")
    calculator = DiscrepancyCalculator(logger=logger)
    
    try:
        processed_df = calculator.process(raw_data_path)
    except Exception as e:
        logger.critical(f"Discrepancy calculation failed: {e}")
        raise

    # 4. Validate Output Schema
    logger.info("Validating output schema...")
    if not validate_output_schema(processed_df):
        error_msg = "Processed data does not match required schema"
        logger.critical(error_msg)
        raise ConfigurationError(error_msg)
    logger.info("Schema validation passed.")

    # 5. Save Processed Data
    output_filename = f"discrepancies_processed.{args.output_format}"
    output_path = processed_dir / output_filename
    
    logger.info(f"Saving processed data to {output_path}...")
    if args.output_format == "csv":
        processed_df.to_csv(output_path, index=False)
    elif args.output_format == "parquet":
        processed_df.to_parquet(output_path, index=False)
    
    logger.info(f"Processed data saved: {output_path}")

    # 6. Compute and save checksum for processed data
    try:
        processed_hash = compute_file_hash(output_path)
        checksum_file = state_dir / "processed_data_checksum.json"
        save_checksums({output_filename: processed_hash}, checksum_file)
        logger.info(f"Saved checksum for {output_filename} to {checksum_file}")
    except Exception as e:
        logger.error(f"Failed to compute/save checksum for processed data: {e}")
        # Non-fatal for pipeline completion, but logged as error
    
    logger.info("Pipeline execution completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
