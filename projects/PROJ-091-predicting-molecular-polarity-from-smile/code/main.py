"""
Main orchestration script for the Molecular Polarity Prediction Pipeline.

This script coordinates the full pipeline execution:
1. Check prerequisites (directories, config, dependencies)
2. Validate 2D-only compliance (no 3D conformer generation)
3. Validate that the descriptor file exists before proceeding
4. Execute the preprocessing and training pipeline steps

Entry point: python -m main or python main.py
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# Local imports matching the project API surface
from utils.logging_config import get_logger, set_log_level
from utils.validators import assert_no_3d_calls
from data.loader import iterate_smiles
from data.preprocess_2d import preprocess_2d
from data.save_descriptors import main as save_descriptors_main
from data.split_data import main as split_data_main
from models.train_lightgbm import main as train_lightgbm_main
from models.evaluate import main as evaluate_main

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Output paths as defined in tasks.md
DESCRIPTORS_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "qm9_smiles.csv"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"

logger = get_logger(__name__)


def check_prerequisites() -> bool:
    """
    Verify that all necessary directories and configuration files exist.

    Returns:
        bool: True if all prerequisites are met, False otherwise.
    """
    logger.info("Checking prerequisites...")
    success = True

    # Check required directories
    required_dirs = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "processed" / "analysis",
        LOGS_DIR,
    ]

    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Required directory missing: {dir_path}")
            success = False
        else:
            logger.debug(f"Directory exists: {dir_path}")

    # Check config file
    if not CONFIG_PATH.exists():
        logger.error(f"Configuration file missing: {CONFIG_PATH}")
        success = False
    else:
        logger.debug(f"Configuration file exists: {CONFIG_PATH}")

    # Check requirements file
    requirements_path = PROJECT_ROOT / "code" / "requirements.txt"
    if not requirements_path.exists():
        logger.error(f"Requirements file missing: {requirements_path}")
        success = False
    else:
        logger.debug(f"Requirements file exists: {requirements_path}")

    if success:
        logger.info("All prerequisites met.")
    else:
        logger.error("Prerequisites check failed.")

    return success


def validate_2d_compliance() -> bool:
    """
    Validate that the pipeline enforces 2D-only constraints.

    This function uses the validator module to ensure no 3D conformer
    generation functions are accessible in the descriptor computation context.

    Returns:
        bool: True if 2D compliance is validated, False otherwise.
    """
    logger.info("Validating 2D-only compliance...")
    try:
        # This will raise an AssertionError if 3D functions are detected
        assert_no_3d_calls()
        logger.info("2D-only compliance validated successfully.")
        return True
    except AssertionError as e:
        logger.error(f"2D compliance validation failed: {e}")
        return False


def validate_descriptors_file() -> bool:
    """
    Verify that the processed descriptors file exists before proceeding to training.

    This is a critical check for task T019 dependency.

    Returns:
        bool: True if the descriptors file exists and is valid, False otherwise.
    """
    logger.info(f"Validating descriptors file: {DESCRIPTORS_PATH}")

    if not DESCRIPTORS_PATH.exists():
        logger.error(
            f"Descriptors file not found: {DESCRIPTORS_PATH}. "
            "Please run the preprocessing pipeline first."
        )
        return False

    try:
        # Attempt to read the file to verify it's not corrupted
        import pyarrow.parquet as pq
        table = pq.read_table(DESCRIPTORS_PATH)
        num_rows = table.num_rows
        num_columns = table.num_columns
        logger.info(
            f"Descriptors file validated: {num_rows} rows, {num_columns} columns."
        )
        return True
    except Exception as e:
        logger.error(f"Failed to validate descriptors file: {e}")
        return False


def run_data_preprocessing(raw_path: Optional[Path] = None) -> bool:
    """
    Execute the data preprocessing pipeline.

    Args:
        raw_path: Optional path to raw SMILES data. Defaults to RAW_DATA_PATH.

    Returns:
        bool: True if preprocessing completed successfully, False otherwise.
    """
    if raw_path is None:
        raw_path = RAW_DATA_PATH

    logger.info(f"Starting data preprocessing from: {raw_path}")

    if not raw_path.exists():
        logger.error(f"Raw data file not found: {raw_path}")
        logger.info("Hint: Run code/data/download_qm9.py to fetch the dataset.")
        return False

    try:
        # Call the preprocessing function which handles:
        # - Descriptor computation
        # - High correlation filtering
        # - NaN handling
        # - Batch processing for memory efficiency
        preprocess_2d(input_path=raw_path, output_path=DESCRIPTORS_PATH)
        logger.info("Data preprocessing completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Data preprocessing failed: {e}", exc_info=True)
        return False


def run_pipeline(args: argparse.Namespace) -> int:
    """
    Execute the full pipeline orchestration.

    Args:
        args: Parsed command line arguments.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    logger.info("Starting Molecular Polarity Prediction Pipeline")
    logger.info(f"Project root: {PROJECT_ROOT}")

    # Step 1: Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Aborting.")
        return 1

    # Step 2: Validate 2D compliance
    if not validate_2d_compliance():
        logger.error("2D compliance validation failed. Aborting.")
        return 1

    # Step 3: Preprocess data if --preprocess flag is set or if descriptors missing
    if args.preprocess or not DESCRIPTORS_PATH.exists():
        if not run_data_preprocessing():
            logger.error("Data preprocessing failed. Aborting.")
            return 1

        # Re-validate descriptors file after preprocessing
        if not validate_descriptors_file():
            logger.error("Descriptors file validation failed after preprocessing. Aborting.")
            return 1
    else:
        # Explicitly validate before training as per T019 requirement
        if not validate_descriptors_file():
            logger.error(
                "Descriptors file missing or invalid. "
                "Run with --preprocess to generate it."
            )
            return 1

    # Step 4: Split data
    logger.info("Splitting data into train/test sets...")
    try:
        split_data_main()
        logger.info("Data splitting completed.")
    except Exception as e:
        logger.error(f"Data splitting failed: {e}", exc_info=True)
        return 1

    # Step 5: Train model
    if not args.skip_training:
        logger.info("Training LightGBM model...")
        try:
            train_lightgbm_main()
            logger.info("Model training completed.")
        except Exception as e:
            logger.error(f"Model training failed: {e}", exc_info=True)
            return 1

    # Step 6: Evaluate model
    if not args.skip_evaluation:
        logger.info("Evaluating model performance...")
        try:
            evaluate_main()
            logger.info("Model evaluation completed.")
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}", exc_info=True)
            return 1

    # Step 7: Run interpretation (SHAP) if requested
    if args.run_interpretation:
        logger.info("Running SHAP interpretation analysis...")
        try:
            from models.interpret import main as interpret_main
            interpret_main()
            logger.info("Interpretation analysis completed.")
        except Exception as e:
            logger.error(f"Interpretation analysis failed: {e}", exc_info=True)
            return 1

    logger.info("Pipeline completed successfully.")
    return 0


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the Molecular Polarity Prediction Pipeline"
    )
    parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Force data preprocessing step"
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Skip model training step"
    )
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip model evaluation step"
    )
    parser.add_argument(
        "--run-interpretation",
        action="store_true",
        help="Run SHAP interpretation analysis"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )

    args = parser.parse_args()

    # Configure logging
    set_log_level(args.log_level)

    # Run the pipeline
    exit_code = run_pipeline(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()