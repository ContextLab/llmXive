"""
Orchestration script for the molecular polarity prediction pipeline.

This script provides the entry point for the full pipeline execution.
It validates prerequisites, ensures 2D compliance, checks for required
artifacts, and executes the pipeline steps in the correct order.
"""
import sys
import os
import pyarrow.parquet as pq
from pathlib import Path
from utils.logging_config import get_logger, set_log_level
from utils.validators import assert_no_3d_calls
from data.loader import iterate_smiles
from data.preprocess_2d import preprocess_2d
from data.split_data import split_data
from models.train_lightgbm import train_lightgbm
from models.evaluate import evaluate_model

# Project root path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger("main")
set_log_level("INFO")

# Hardcoded seeds for reproducibility (per T004 constraint)
GLOBAL_SEED = 42

def check_prerequisites():
    """
    Check that all required directories and initial files exist.
    Returns True if all prerequisites are met, False otherwise.
    """
    logger.info("Checking prerequisites...")
    
    required_dirs = [RAW_DIR, PROCESSED_DIR, LOGS_DIR]
    for d in required_dirs:
        if not d.exists():
            logger.error(f"Required directory missing: {d}")
            return False
    
    # Check for QM9 data file (expected location)
    qm9_file = RAW_DIR / "qm9_smiles.csv"
    if not qm9_file.exists():
        logger.warning(f"QM9 data file not found at {qm9_file}. "
                     "This is expected if data has not been downloaded yet.")
        return False
    
    logger.info("Prerequisites check passed.")
    return True

def validate_2d_compliance():
    """
    Validate that no 3D conformer generation functions are called.
    Uses the validator utility to check the current execution context.
    """
    logger.info("Validating 2D compliance...")
    try:
        assert_no_3d_calls()
        logger.info("2D compliance validation passed.")
        return True
    except AssertionError as e:
        logger.error(f"2D compliance validation failed: {e}")
        return False

def validate_descriptors_file():
    """
    Validate that the processed descriptors file exists and is valid.
    This is the key check before proceeding to model training (T019).
    
    Returns:
        bool: True if file exists and is valid, False otherwise.
    """
    logger.info("Validating descriptors file...")
    
    descriptors_file = PROCESSED_DIR / "descriptors.parquet"
    
    if not descriptors_file.exists():
        logger.error(f"Descriptors file not found: {descriptors_file}")
        logger.error("Please run the preprocessing pipeline first.")
        return False
    
    try:
        # Try to read the file to ensure it's valid
        table = pq.read_table(descriptors_file)
        num_rows = table.num_rows
        num_cols = table.num_columns
        
        if num_rows == 0:
            logger.error("Descriptors file is empty.")
            return False
        
        logger.info(f"Descriptors file validated: {num_rows} rows, {num_cols} columns")
        return True
        
    except Exception as e:
        logger.error(f"Error reading descriptors file: {e}")
        return False

def run_pipeline():
    """
    Execute the full pipeline:
    1. Download data (if not present)
    2. Preprocess 2D descriptors
    3. Split data
    4. Train model
    5. Evaluate model
    
    Returns:
        bool: True if pipeline completed successfully, False otherwise.
    """
    logger.info("Starting pipeline execution...")
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Aborting.")
        return False
    
    # Step 2: Validate 2D compliance
    if not validate_2d_compliance():
        logger.error("2D compliance validation failed. Aborting.")
        return False
    
    # Step 3: Run preprocessing (T013-T018)
    logger.info("Running preprocessing...")
    try:
        preprocess_2d(
            input_path=RAW_DIR / "qm9_smiles.csv",
            output_path=PROCESSED_DIR / "descriptors.parquet"
        )
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return False
    
    # Step 4: Validate descriptors file (T019 check)
    if not validate_descriptors_file():
        logger.error("Descriptors validation failed. Aborting.")
        return False
    
    # Step 5: Split data (T022)
    logger.info("Splitting data...")
    try:
        split_data(
            input_path=PROCESSED_DIR / "descriptors.parquet",
            output_dir=PROCESSED_DIR
        )
    except Exception as e:
        logger.error(f"Data splitting failed: {e}")
        return False
    
    # Step 6: Train model (T023-T026)
    logger.info("Training model...")
    try:
        train_lightgbm(
            data_dir=PROCESSED_DIR,
            output_path=PROCESSED_DIR / "model.pkl"
        )
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return False
    
    # Step 7: Evaluate model (T027)
    logger.info("Evaluating model...")
    try:
        evaluate_model(
            model_path=PROCESSED_DIR / "model.pkl",
            data_dir=PROCESSED_DIR
        )
    except Exception as e:
        logger.error(f"Model evaluation failed: {e}")
        return False
    
    logger.info("Pipeline completed successfully!")
    return True

def main():
    """
    Main entry point for the pipeline.
    Parses command line arguments and executes the appropriate action.
    """
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "run":
            success = run_pipeline()
            sys.exit(0 if success else 1)
        elif command == "validate":
            success = validate_descriptors_file()
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Unknown command: {command}")
            print("Usage: python main.py [run|validate]")
            sys.exit(1)
    else:
        # Default to running the pipeline
        success = run_pipeline()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()