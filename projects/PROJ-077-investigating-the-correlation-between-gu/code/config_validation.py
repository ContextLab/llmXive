import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories, INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT
from logging_config import get_logger, log_pipeline_start, log_warning, log_provenance

def validate_directories(required_dirs: List[str]) -> bool:
    """
    Validate that all required directories exist.
    If a directory does not exist, attempt to create it.
    Returns True if all directories are present (or created), False otherwise.
    """
    logger = get_logger()
    all_valid = True
    
    for dir_path in required_dirs:
        path_obj = Path(dir_path)
        if not path_obj.exists():
            logger.warning(f"Directory missing: {dir_path}. Attempting creation.")
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                log_provenance(f"Created directory: {dir_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                all_valid = False
        else:
            if not path_obj.is_dir():
                logger.error(f"Path exists but is not a directory: {dir_path}")
                all_valid = False
    
    return all_valid

def validate_input_files(file_paths: List[str]) -> bool:
    """
    Validate that all required input files exist.
    Returns True if all files exist, False otherwise.
    """
    logger = get_logger()
    missing_files = []
    
    for file_path in file_paths:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            log_warning(f"Required input file missing: {file_path}")
    
    if missing_files:
        logger.error(f"Missing required input files: {missing_files}")
        return False
    
    log_provenance("All required input files verified.")
    return True

def validate_configuration() -> bool:
    """
    Main configuration validation function.
    Checks:
    1. Required directories (data/raw, data/processed, code, tests)
    2. Required input files defined in INPUT_PATHS
    3. Basic config parameters (RANDOM_SEED, SAMPLE_LIMIT)
    
    Returns True if validation passes, False if any check fails.
    """
    logger = get_logger()
    log_pipeline_start("Configuration Validation")
    
    is_valid = True
    
    # 1. Validate directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "data/processed/plots"
    ]
    if not validate_directories(required_dirs):
        is_valid = False
    
    # 2. Validate input files
    # We expect the raw data files to exist in data/raw/
    # The specific files depend on the dataset, but we check for the existence
    # of the directory and common expected files if defined in INPUT_PATHS
    input_files_to_check = []
    
    # Check for standard expected files based on project context
    # If INPUT_PATHS is a dict of names to paths, we check those paths
    if isinstance(INPUT_PATHS, dict):
        for key, path in INPUT_PATHS.items():
            if isinstance(path, str):
                input_files_to_check.append(path)
            elif isinstance(path, list):
                input_files_to_check.extend(path)
    
    # Fallback: check for common expected files if INPUT_PATHS is empty or not set
    if not input_files_to_check:
        input_files_to_check = [
            "data/raw/microbiome_data.csv",
            "data/raw/cognitive_data.csv"
        ]
    
    if not validate_input_files(input_files_to_check):
        is_valid = False
    
    # 3. Validate config parameters
    if not isinstance(RANDOM_SEED, int) or RANDOM_SEED < 0:
        logger.error(f"Invalid RANDOM_SEED: {RANDOM_SEED}. Must be a non-negative integer.")
        is_valid = False
        
    if not isinstance(SAMPLE_LIMIT, int) or SAMPLE_LIMIT <= 0:
        logger.error(f"Invalid SAMPLE_LIMIT: {SAMPLE_LIMIT}. Must be a positive integer.")
        is_valid = False
    
    if is_valid:
        log_provenance("Configuration validation successful.")
    else:
        log_warning("Configuration validation failed. Pipeline cannot start.")
    
    return is_valid

def main():
    """
    Entry point for running configuration validation as a script.
    """
    success = validate_configuration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
