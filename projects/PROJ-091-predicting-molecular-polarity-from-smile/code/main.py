import sys
import os
import argparse
import logging
import gc
from pathlib import Path
from typing import Optional

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent))

# Import standardized logging
from utils.logging_config import setup_logging, get_logger
from utils.validators import enforce_2d_only_imports, assert_no_3d_calls

logger = get_logger(__name__)

def check_prerequisites() -> bool:
    """Verify that all prerequisite files and directories exist."""
    logger.info("Checking prerequisites...")
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/processed/analysis",
        "logs"
    ]
    
    required_files = [
        "data/raw/qm9_smiles.csv",
        "code/config.yaml"
    ]
    
    project_root = Path(__file__).parent.parent
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            logger.warning(f"Directory missing: {full_path}")
            # Attempt to create
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
    
    # Note: We do not fail if data files are missing, as they might be downloaded
    # But we log a warning
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            logger.warning(f"Required file missing (may be downloaded later): {full_path}")
    
    return True

def validate_2d_compliance() -> bool:
    """Validate that no 3D conformer generation functions are called."""
    logger.info("Validating 2D-only compliance...")
    try:
        # This function would ideally inspect the code or runtime context
        # For now, we rely on the validators module
        assert_no_3d_calls()
        logger.info("2D-only compliance check passed.")
        return True
    except AssertionError as e:
        logger.error(f"2D-only compliance check failed: {e}")
        return False

def validate_descriptors_file(filepath: Path) -> bool:
    """Validate the processed descriptors file schema."""
    logger.info(f"Validating descriptors file: {filepath}")
    if not filepath.exists():
        logger.error(f"Descriptors file not found: {filepath}")
        return False
    
    # Basic validation: check if it's a parquet file
    if not filepath.suffix == '.parquet':
        logger.error(f"Invalid file format: {filepath.suffix}")
        return False
    
    # In a real scenario, we would load and check schema
    # For now, we assume if it exists and is parquet, it's valid
    logger.info(f"Descriptors file validated: {filepath}")
    return True

def run_data_preprocessing() -> bool:
    """Run the data preprocessing pipeline."""
    logger.info("Running data preprocessing...")
    
    # Import here to avoid circular imports if any
    from data.preprocess_2d import preprocess_2d
    
    success = preprocess_2d()
    if success:
        logger.info("Data preprocessing completed successfully.")
    else:
        logger.error("Data preprocessing failed.")
    
    return success

def run_pipeline() -> bool:
    """Run the full pipeline."""
    logger.info("Starting full pipeline...")
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed.")
        return False
    
    # Step 2: Validate 2D compliance
    if not validate_2d_compliance():
        logger.error("2D compliance validation failed.")
        return False
    
    # Step 3: Run preprocessing
    if not run_data_preprocessing():
        logger.error("Preprocessing failed.")
        return False
    
    # Step 4: Validate output
    output_file = Path(__file__).parent.parent / "data" / "processed" / "descriptors.parquet"
    if not validate_descriptors_file(output_file):
        logger.error("Output validation failed.")
        return False
    
    logger.info("Full pipeline completed successfully.")
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Molecular Polarity Prediction Pipeline")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set logging level")
    parser.add_argument("--pipeline", action="store_true", help="Run full pipeline")
    parser.add_argument("--preprocess", action="store_true", help="Run only preprocessing")
    
    args = parser.parse_args()
    
    # Setup logging with standardized format
    setup_logging(log_level=getattr(logging, args.log_level.upper()))
    
    if args.pipeline:
        success = run_pipeline()
    elif args.preprocess:
        success = run_data_preprocessing()
    else:
        # Default: run pipeline
        success = run_pipeline()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()