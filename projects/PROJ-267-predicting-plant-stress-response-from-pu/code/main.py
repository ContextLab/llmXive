"""
Main entry point for the plant stress response prediction pipeline.

This script orchestrates the full pipeline: Data Ingestion -> Preprocessing -> Modeling -> Reporting.
It includes a critical pre-flight check (T042) to ensure data dependencies are met before training.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Import project configuration and logging
from utils.config import get_project_root, get_data_path, get_log_path
from utils.logging_config import setup_logging, get_logger

# Import pipeline stages
from data_ingestion.pipeline import run_pipeline
from data_ingestion.sanity_check import validate_dataset_integrity
from data_ingestion.sample_check import evaluate_data_sufficiency
from modeling.train import run_training_pipeline
from reporting.generate_report import generate_summary_report

def check_data_dependency():
    """
    T042: Verify Data Flow Order.
    
    Ensures 'data/processed/merged_matrix.csv' exists and is non-empty
    before proceeding to the modeling stage.
    
    Raises:
        SystemExit: If the file is missing or empty.
    """
    project_root = get_project_root()
    data_path = get_data_path()
    merged_file = data_path / "processed" / "merged_matrix.csv"
    
    logger = get_logger()
    
    logger.info("Running T042: Pre-flight data dependency check...")
    
    if not merged_file.exists():
        error_msg = "Data Dependency Error: Preprocessing did not complete successfully. " \
                    f"Expected file '{merged_file}' not found."
        logger.error(error_msg)
        # Halt execution as per requirement
        raise SystemExit(error_msg)
    
    file_size = merged_file.stat().st_size
    if file_size == 0:
        error_msg = "Data Dependency Error: Preprocessing did not complete successfully. " \
                    f"Expected file '{merged_file}' is empty."
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    # Basic sanity check: ensure it's not just a header with no data
    try:
        import pandas as pd
        df = pd.read_csv(merged_file, nrows=1)
        # If we get here, file has at least a header. 
        # A more robust check could read the whole file if it's small, 
        # but for large files, checking size > header_size is usually enough.
        # However, to be safe against a file that is *only* a header (0 rows),
        # we check the row count.
        df_full = pd.read_csv(merged_file)
        if len(df_full) == 0:
            error_msg = "Data Dependency Error: Preprocessing did not complete successfully. " \
                        f"File '{merged_file}' contains no data rows (only headers)."
            logger.error(error_msg)
            raise SystemExit(error_msg)
            
        logger.info(f"Data dependency check passed. Found {len(df_full)} rows in '{merged_file}'.")
        return True
        
    except Exception as e:
        error_msg = f"Data Dependency Error: Could not read or validate '{merged_file}': {str(e)}"
        logger.error(error_msg)
        raise SystemExit(error_msg)

def main():
    parser = argparse.ArgumentParser(description="Plant Stress Response Prediction Pipeline")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip data ingestion and start at modeling")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip modeling and start at reporting")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Setup logging
    log_path = get_log_path()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level=log_level)
    logger = get_logger()

    logger.info("="*60)
    logger.info("Starting Plant Stress Response Prediction Pipeline")
    logger.info("="*60)

    try:
        # Phase 1: Data Ingestion (Optional skip)
        if not args.skip_ingestion:
            logger.info("Phase 1: Running Data Ingestion Pipeline...")
            run_pipeline()
            
            # Run sanity checks
            logger.info("Running data integrity checks...")
            validate_dataset_integrity()
            
            logger.info("Running sample sufficiency checks...")
            evaluate_data_sufficiency()
        else:
            logger.info("Skipping Data Ingestion (as requested).")

        # Phase 1.5: T042 - Data Flow Order Check (CRITICAL BEFORE MODELING)
        # This must run before any modeling code, even if ingestion was skipped
        # (assuming the user has manually placed the data there).
        logger.info("Phase 1.5: Verifying Data Flow Order (T042)...")
        check_data_dependency()

        # Phase 2: Modeling
        if not args.skip_modeling:
            logger.info("Phase 2: Running Modeling Pipeline...")
            run_training_pipeline()
        else:
            logger.info("Skipping Modeling (as requested).")

        # Phase 3: Reporting
        logger.info("Phase 3: Generating Final Report...")
        generate_summary_report()

        logger.info("="*60)
        logger.info("Pipeline completed successfully.")
        logger.info("="*60)

    except SystemExit as e:
        # Re-raise SystemExit for clean termination with error message
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()