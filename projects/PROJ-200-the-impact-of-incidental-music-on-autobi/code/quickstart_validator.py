"""
T046: Quickstart Validation Script

This script validates the end-to-end pipeline execution as described in quickstart.md.
It runs the full pipeline from data ingestion to final results generation and verifies
that all expected output files are created with valid content.

The script must complete within 6 hours on standard hardware.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_project_root, get_config_dict, ensure_directories
from utils import setup_logging, get_logger
from main import run_pipeline
from state_manager import load_state, verify_all

# Configuration
MAX_EXECUTION_TIME_SECONDS = 6 * 3600  # 6 hours
REQUIRED_OUTPUT_FILES = [
    "data/processed/ingested_cohort.parquet",
    "data/processed/user_track_pairs.parquet",
    "data/final/regression_summary.csv",
    "data/final/sensitivity_analysis.csv",
    "data/final/permutation_results.csv",
]

# Setup logging
logger = get_logger(__name__)

def check_prerequisites() -> Tuple[bool, List[str]]:
    """Check that all prerequisites are met before running validation."""
    errors = []
    project_root = get_project_root()
    
    # Check required directories exist
    required_dirs = [
        "data/raw",
        "data/processed", 
        "data/final",
        "data/final/plots"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            errors.append(f"Required directory missing: {dir_path}")
    
    # Check required input files exist (if they should be pre-downloaded)
    # Note: If data ingestion handles downloading, this check can be skipped
    
    # Check required Python packages
    required_packages = [
        "pandas", "numpy", "scikit-learn", "statsmodels", 
        "python-Levenshtein", "pyyaml", "tqdm", "scipy", "pyarrow"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            errors.append(f"Missing required package: {package}")
    
    return len(errors) == 0, errors

def validate_output_file(file_path: Path, min_size_bytes: int = 0) -> Tuple[bool, str]:
    """Validate that an output file exists and contains valid data."""
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
    
    file_size = file_path.stat().st_size
    if file_size < min_size_bytes:
        return False, f"File too small ({file_size} bytes): {file_path}"
    
    # Validate file content based on extension
    if file_path.suffix == ".parquet":
        try:
            df = pd.read_parquet(file_path)
            if len(df) == 0:
                return False, f"Parquet file is empty: {file_path}"
            logger.info(f"Validated parquet: {file_path.name} ({len(df)} rows, {file_size} bytes)")
        except Exception as e:
            return False, f"Invalid parquet file {file_path}: {str(e)}"
            
    elif file_path.suffix == ".csv":
        try:
            df = pd.read_csv(file_path)
            if len(df) == 0:
                return False, f"CSV file is empty: {file_path}"
            logger.info(f"Validated CSV: {file_path.name} ({len(df)} rows, {file_size} bytes)")
        except Exception as e:
            return False, f"Invalid CSV file {file_path}: {str(e)}"
    
    elif file_path.suffix == ".yaml" or file_path.suffix == ".yml":
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                if data is None:
                    return False, f"YAML file is empty: {file_path}"
            logger.info(f"Validated YAML: {file_path.name} ({file_size} bytes)")
        except Exception as e:
            return False, f"Invalid YAML file {file_path}: {str(e)}"
    
    else:
        logger.info(f"File exists: {file_path.name} ({file_size} bytes)")
    
    return True, "OK"

def run_pipeline_validation() -> Tuple[bool, str]:
    """Run the full pipeline and validate outputs."""
    start_time = time.time()
    
    try:
        logger.info("Starting pipeline validation...")
        logger.info(f"Maximum allowed execution time: {MAX_EXECUTION_TIME_SECONDS / 3600:.1f} hours")
        
        # Run the pipeline
        run_pipeline()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed_time / 3600:.2f} hours")
        
        # Check execution time
        if elapsed_time > MAX_EXECUTION_TIME_SECONDS:
            return False, f"Pipeline took {elapsed_time / 3600:.2f} hours, exceeding 6-hour limit"
        
        return True, f"Pipeline completed in {elapsed_time / 3600:.2f} hours"
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Pipeline failed after {elapsed_time / 3600:.2f} hours: {str(e)}")
        return False, f"Pipeline execution failed: {str(e)}"

def validate_all_outputs() -> Tuple[bool, List[str]]:
    """Validate all required output files."""
    project_root = get_project_root()
    errors = []
    valid_count = 0
    
    logger.info("Validating output files...")
    
    for relative_path in REQUIRED_OUTPUT_FILES:
        file_path = project_root / relative_path
        success, message = validate_output_file(file_path)
        
        if success:
            valid_count += 1
        else:
            errors.append(message)
    
    logger.info(f"Output validation: {valid_count}/{len(REQUIRED_OUTPUT_FILES)} files valid")
    return len(errors) == 0, errors

def validate_state_tracking() -> Tuple[bool, str]:
    """Validate that state.yaml contains checksums for derived files."""
    project_root = get_project_root()
    state_file = project_root / "state.yaml"
    
    if not state_file.exists():
        return False, "state.yaml does not exist"
    
    try:
        state = load_state()
        if not state or "files" not in state or len(state["files"]) == 0:
            return False, "state.yaml exists but contains no file checksums"
        
        logger.info(f"State tracking verified: {len(state['files'])} files registered")
        return True, "OK"
    except Exception as e:
        return False, f"Failed to load state.yaml: {str(e)}"

def main():
    """Main validation entry point."""
    setup_logging(level=logging.INFO)
    project_root = get_project_root()
    logger.info(f"Starting quickstart validation for project: {project_root}")
    
    # Step 1: Check prerequisites
    logger.info("=" * 60)
    logger.info("Step 1: Checking prerequisites")
    prereqs_ok, prereq_errors = check_prerequisites()
    
    if not prereqs_ok:
        logger.error("Prerequisites check failed:")
        for error in prereq_errors:
            logger.error(f"  - {error}")
        print("\nValidation FAILED: Prerequisites not met")
        print("Errors:")
        for error in prereq_errors:
            print(f"  - {error}")
        return 1
    
    logger.info("Prerequisites check PASSED")
    
    # Step 2: Run pipeline
    logger.info("=" * 60)
    logger.info("Step 2: Running pipeline")
    pipeline_ok, pipeline_message = run_pipeline_validation()
    
    if not pipeline_ok:
        logger.error(f"Pipeline validation failed: {pipeline_message}")
        print(f"\nValidation FAILED: {pipeline_message}")
        return 1
    
    logger.info(f"Pipeline validation PASSED: {pipeline_message}")
    
    # Step 3: Validate output files
    logger.info("=" * 60)
    logger.info("Step 3: Validating output files")
    outputs_ok, output_errors = validate_all_outputs()
    
    if not outputs_ok:
        logger.error("Output validation failed:")
        for error in output_errors:
            logger.error(f"  - {error}")
        print("\nValidation FAILED: Output files incomplete or invalid")
        print("Errors:")
        for error in output_errors:
            print(f"  - {error}")
        return 1
    
    logger.info("Output validation PASSED")
    
    # Step 4: Validate state tracking
    logger.info("=" * 60)
    logger.info("Step 4: Validating state tracking")
    state_ok, state_message = validate_state_tracking()
    
    if not state_ok:
        logger.error(f"State tracking validation failed: {state_message}")
        print(f"\nValidation FAILED: {state_message}")
        return 1
    
    logger.info("State tracking validation PASSED")
    
    # Final summary
    logger.info("=" * 60)
    logger.info("VALIDATION COMPLETE: ALL CHECKS PASSED")
    print("\n" + "=" * 60)
    print("QUICKSTART VALIDATION SUCCESSFUL")
    print("=" * 60)
    print(f"Pipeline executed successfully within time limit")
    print(f"All required output files generated and validated")
    print(f"State tracking mechanism verified")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
