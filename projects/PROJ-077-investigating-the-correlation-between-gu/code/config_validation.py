"""
Configuration validation module for the Gut Microbiome and Cognitive Performance analysis pipeline.
Validates directories, input files, and overall configuration before pipeline execution.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories, INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, DQS_REQUIRED
from logging_config import get_logger, log_provenance, log_warning

logger = get_logger(__name__)

def validate_directories() -> bool:
    """
    Validates that all required directories exist.
    Creates them if they do not exist.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("Validating directory structure...")
    try:
        ensure_directories()
        logger.info("Directory structure validated successfully.")
        return True
    except Exception as e:
        logger.error(f"Directory validation failed: {str(e)}")
        return False

def validate_input_files() -> bool:
    """
    Validates that all required input files exist and are non-empty.
    Raises FileNotFoundError if any required file is missing or empty.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("Validating input files...")
    missing_files = []
    empty_files = []
    
    for file_type, file_path in INPUT_PATHS.items():
        if not os.path.exists(file_path):
            missing_files.append(str(file_path))
            continue
        
        # Check if file is non-empty
        if os.path.getsize(file_path) == 0:
            empty_files.append(str(file_path))
            continue
        
        logger.debug(f"Input file '{file_type}' validated: {file_path}")
    
    if missing_files:
        error_msg = f"Missing required input files: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    if empty_files:
        error_msg = f"Empty required input files: {', '.join(empty_files)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("All input files validated successfully.")
    return True

def validate_configuration() -> bool:
    """
    Validates the overall configuration including directories and input files.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    logger.info("Starting configuration validation...")
    
    if not validate_directories():
        logger.error("Directory validation failed.")
        return False
    
    try:
        if not validate_input_files():
            logger.error("Input file validation failed.")
            return False
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        return False
    
    logger.info("Configuration validation completed successfully.")
    log_provenance("Configuration Validation", {
        "random_seed": RANDOM_SEED,
        "sample_limit": SAMPLE_LIMIT,
        "dqs_required": DQS_REQUIRED
    })
    return True

def main():
    """
    Main entry point for configuration validation script.
    """
    logger.info("=" * 80)
    logger.info("Configuration Validation Module")
    logger.info("=" * 80)
    
    success = validate_configuration()
    
    if success:
        logger.info("Configuration validation PASSED.")
        return 0
    else:
        logger.error("Configuration validation FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())