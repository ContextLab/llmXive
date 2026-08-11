"""
Configuration Validation Module.
Validates that required directories and input files exist and are non-empty
before pipeline execution begins.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_directories, INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning

logger = get_logger(__name__)

def validate_directories() -> bool:
    """
    Ensures all required directories exist.
    Returns True if all directories are present or created successfully.
    """
    try:
        ensure_directories()
        logger.info("Directory validation passed: All required directories exist.")
        return True
    except Exception as e:
        logger.error(f"Directory validation failed: {str(e)}")
        return False

def validate_input_files() -> bool:
    """
    Checks that all required input files defined in INPUT_PATHS exist
    and are non-empty (size > 0 bytes).
    Raises FileNotFoundError if any file is missing or empty.
    Returns True if all validations pass.
    """
    missing_files = []
    empty_files = []

    for key, path_str in INPUT_PATHS.items():
        path = Path(path_str)
        if not path.exists():
            missing_files.append(f"{key}: {path_str}")
        elif path.stat().st_size == 0:
            empty_files.append(f"{key}: {path_str}")

    if missing_files:
        error_msg = f"Missing required input files:\n" + "\n".join(missing_files)
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if empty_files:
        error_msg = f"Empty required input files (0 bytes):\n" + "\n".join(empty_files)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Input file validation passed: All required files exist and are non-empty.")
    return True

def validate_configuration() -> bool:
    """
    Runs full configuration validation:
    1. Validates directories exist.
    2. Validates input files exist and are non-empty.
    3. Validates configuration constants (RANDOM_SEED, SAMPLE_LIMIT).

    Returns True if all checks pass, False otherwise.
    """
    logger.info("Starting configuration validation...")

    # Validate directories
    if not validate_directories():
        return False

    # Validate input files
    try:
        validate_input_files()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Input file validation failed: {str(e)}")
        return False

    # Validate configuration constants
    if not isinstance(RANDOM_SEED, int) or RANDOM_SEED < 0:
        logger.error(f"Invalid RANDOM_SEED: {RANDOM_SEED}. Must be a non-negative integer.")
        return False

    if not isinstance(SAMPLE_LIMIT, int) or SAMPLE_LIMIT <= 0:
        logger.error(f"Invalid SAMPLE_LIMIT: {SAMPLE_LIMIT}. Must be a positive integer.")
        return False

    logger.info("Configuration validation completed successfully.")
    log_provenance("Configuration Validation", {
        "status": "PASSED",
        "random_seed": RANDOM_SEED,
        "sample_limit": SAMPLE_LIMIT
    })
    return True

def main():
    """
    Entry point for running configuration validation as a standalone script.
    """
    logger.info("Running configuration validation script...")
    success = validate_configuration()
    if success:
        logger.info("Configuration validation PASSED.")
        return 0
    else:
        logger.error("Configuration validation FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
