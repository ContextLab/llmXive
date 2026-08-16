import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from utils.logging_config import get_logger
from utils.validators import assert_no_3d_calls
from data.preprocess_2d import preprocess_2d
from data.save_descriptors import verify_schema

logger = get_logger(__name__)

def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    required_dirs = ["data/raw", "data/processed", "data/processed/analysis", "logs"]
    for d in required_dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {d}")
    return True

def validate_2d_compliance(filepath: Path) -> bool:
    """
    Validate that the pipeline execution context adheres to 2D-only constraints.
    Uses the runtime validator from utils.validators to ensure no 3D functions
    (like EmbedMolecule or Get3DConformer) are called during descriptor computation.
    """
    logger.info("Running 2D compliance check via runtime validator...")
    try:
        # assert_no_3d_calls checks the current execution frame and imports
        # to ensure no prohibited 3D functions are active or imported.
        assert_no_3d_calls()
        logger.info("2D compliance check passed: No 3D calls detected.")
        return True
    except AssertionError as e:
        logger.critical(f"2D compliance check FAILED: {e}")
        return False

def validate_descriptors_file(filepath: Path) -> bool:
    """Validate the descriptors file schema and existence."""
    if not filepath.exists():
        logger.error(f"Descriptors file not found: {filepath}")
        return False

    logger.info(f"Validating descriptors file: {filepath}")
    return verify_schema(filepath)

def run_data_preprocessing(input_path: Path, output_path: Path) -> bool:
    """Run data preprocessing."""
    try:
        preprocess_2d(input_path, output_path)
        return True
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return False

def run_pipeline(input_path: Optional[Path] = None) -> bool:
    """
    Run the full pipeline with strict validation.
    
    1. Checks prerequisites.
    2. Runs preprocessing.
    3. Validates 2D compliance (no 3D calls).
    4. Validates the output descriptors file exists and schema is correct.
    """
    logger.info("Starting pipeline")
    if not check_prerequisites():
        return False
    
    if input_path is None:
        input_path = Path("data/raw/qm9_processed.parquet")
    output_path = Path("data/processed/descriptors.parquet")
    
    # Run preprocessing
    if not run_data_preprocessing(input_path, output_path):
        return False
    
    # CRITICAL: Validate 2D compliance immediately after processing
    # This ensures the generated data did not involve 3D conformers
    if not validate_2d_compliance(output_path):
        logger.critical("Pipeline halted: 2D compliance validation failed.")
        return False
    
    # CRITICAL: Validate the output file exists and matches schema
    if not validate_descriptors_file(output_path):
        logger.critical("Pipeline halted: Descriptors file validation failed.")
        return False
    
    logger.info("Pipeline completed successfully with all validations passed.")
    return True

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Molecular Polarity Prediction Pipeline")
    parser.add_argument("--input", type=str, help="Input data path")
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    success = run_pipeline(input_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()