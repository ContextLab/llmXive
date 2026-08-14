import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Import existing utilities from the project API surface
from utils.logging_config import get_logger, set_log_level
from utils.validators import assert_no_3d_calls
from data.preprocess_2d import preprocess_2d
from data.loader import iterate_smiles
from data.feature_clustering import run_feature_clustering_analysis

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger(__name__)

def check_prerequisites():
    """Verify that essential directories and configuration files exist."""
    logger.info("Checking prerequisites...")
    required_dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "processed" / "analysis",
        PROJECT_ROOT / "logs",
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Prerequisites check passed.")

def validate_2d_compliance():
    """
    Runtime assertion to verify the pipeline executes without 3D calls.
    This function uses the validator module to enforce 2D-only constraints.
    """
    logger.info("Validating 2D compliance (no 3D calls)...")
    try:
        # This function from utils.validators checks for forbidden 3D imports/calls
        assert_no_3d_calls()
        logger.info("2D compliance validation passed: No 3D calls detected.")
    except AssertionError as e:
        logger.error(f"2D compliance validation FAILED: {e}")
        raise

def validate_descriptors_file():
    """
    Validate that the processed descriptors file exists and contains valid data.
    Checks for existence, non-empty content, and basic schema integrity.
    This function satisfies T019's requirement to verify the output before downstream tasks.
    """
    output_path = PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
    logger.info(f"Validating descriptors file: {output_path}")

    if not output_path.exists():
        error_msg = f"Descriptors file missing: {output_path}. " \
                    "Pipeline cannot proceed without valid processed data."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if output_path.stat().st_size == 0:
        error_msg = f"Descriptors file is empty: {output_path}."
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        import pyarrow.parquet as pq
        table = pq.read_table(output_path)
        if table.num_rows == 0:
            error_msg = f"Descriptors file has 0 rows: {output_path}."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check for required columns (SMILES and target dipole)
        required_cols = {'smiles', 'mu'}
        if not required_cols.issubset(set(table.column_names)):
            missing = required_cols - set(table.column_names)
            error_msg = f"Descriptors file missing required columns: {missing}."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Descriptors file validation passed: {table.num_rows} rows, {table.num_columns} columns.")
        return True

    except Exception as e:
        error_msg = f"Failed to read/validate descriptors file: {e}"
        logger.error(error_msg)
        raise

def run_data_preprocessing():
    """Execute the full 2D descriptor generation pipeline."""
    logger.info("Starting data preprocessing...")
    
    # Run the core preprocessing logic from T014/T015/T016/T017/T018
    # This function is expected to generate data/processed/descriptors.parquet
    preprocess_2d()
    
    logger.info("Data preprocessing completed.")

def run_pipeline():
    """
    Orchestrate the full pipeline with strict validation steps.
    1. Check prerequisites.
    2. Validate 2D compliance (no 3D calls).
    3. Run data preprocessing.
    4. Validate the resulting descriptors file.
    """
    logger.info("=== Starting Molecular Polarity Pipeline ===")
    
    # Step 1: Setup
    check_prerequisites()

    # Step 2: Strict 2D Compliance Check (T019 Requirement)
    # This asserts that no 3D conformer generation or 3D descriptors are used.
    validate_2d_compliance()

    # Step 3: Generate Data
    run_data_preprocessing()

    # Step 4: Validate Output (T019 Requirement)
    # Ensures the pipeline produced a valid parquet file before downstream tasks.
    validate_descriptors_file()

    logger.info("=== Pipeline Completed Successfully ===")

def main():
    parser = argparse.ArgumentParser(description="Molecular Polarity Prediction Pipeline")
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    args = parser.parse_args()

    set_log_level(args.log_level)
    
    try:
        run_pipeline()
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()