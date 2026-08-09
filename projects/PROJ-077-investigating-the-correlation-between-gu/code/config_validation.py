import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories, INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT
from logging_config import get_logger, log_pipeline_start, log_warning, log_provenance

def validate_directories() -> bool:
    """
    Ensure all required directories exist.
    Returns True if all directories exist or were created successfully.
    """
    logger = get_logger()
    logger.info("Validating directory structure...")
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/processed/plots",
        "code",
        "tests",
        "tests/fixtures",
        "docs"
    ]
    
    all_valid = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                log_provenance(f"Created directory: {dir_path}")
                logger.info(f"Created directory: {dir_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                all_valid = False
        else:
            logger.debug(f"Directory exists: {dir_path}")
    
    return all_valid

def validate_input_files() -> bool:
    """
    Check that required input files exist in data/raw.
    Returns True if all mandatory files are present.
    """
    logger = get_logger()
    logger.info("Validating input files...")
    
    # Mandatory files based on the project plan (T011, T012, T014b)
    # We check for the existence of the primary data sources.
    # If specific filenames vary, the config INPUT_PATHS should be updated,
    # but we check for the expected standard names defined in the plan context.
    mandatory_files = [
        "microbiome_data.csv",
        "cognitive_data.csv",
        "participant_metadata.csv"
    ]
    
    # Optional files that trigger specific logic (e.g., DQS)
    optional_files = [
        "dietary_data.csv"
    ]
    
    missing_mandatory = []
    found_optional = []
    
    for filename in mandatory_files:
        file_path = Path("data/raw") / filename
        if not file_path.exists():
            missing_mandatory.append(filename)
        else:
            logger.debug(f"Mandatory file found: {file_path}")
    
    for filename in optional_files:
        file_path = Path("data/raw") / filename
        if file_path.exists():
            found_optional.append(filename)
            logger.info(f"Optional file found: {file_path} (DQS calculation will be attempted)")
        else:
            logger.warning(f"Optional file missing: {file_path} (DQS calculation skipped)")

    if missing_mandatory:
        logger.error(f"Missing mandatory input files: {missing_mandatory}")
        log_warning(f"Pipeline cannot proceed without mandatory files: {missing_mandatory}")
        return False
    
    if found_optional:
        log_provenance(f"Optional files detected: {found_optional}")
    
    return True

def validate_configuration() -> bool:
    """
    Run all validation checks: directories and input files.
    Returns True if the configuration is valid and the pipeline can proceed.
    """
    logger = get_logger()
    log_pipeline_start("Configuration Validation")
    
    # 1. Validate Directory Structure
    dirs_ok = validate_directories()
    if not dirs_ok:
        logger.critical("Directory validation failed. Aborting.")
        return False
    
    # 2. Validate Input Files
    files_ok = validate_input_files()
    if not files_ok:
        logger.critical("Input file validation failed. Aborting.")
        return False
    
    log_provenance("Configuration validation successful. All checks passed.")
    return True

def main():
    """
    Entry point for running configuration validation standalone.
    """
    success = validate_configuration()
    if success:
        print("Configuration validation PASSED.")
        sys.exit(0)
    else:
        print("Configuration validation FAILED. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()