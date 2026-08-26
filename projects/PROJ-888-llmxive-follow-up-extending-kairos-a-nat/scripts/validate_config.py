"""
Validation script for code/config.py.
Verifies that configuration constants are correctly defined and accessible.
Outputs a validation log to logs/config_validation.log.
"""
import sys
import os
import json
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import (
    ensure_dirs,
    SEED,
    QUANTIZATION_LEVELS,
    NOISE_STDS,
    SUBSET_SIZE,
    MAX_RAM_GB,
    MAX_TIME_HOURS,
    INFER_HORIZONS,
    get_config_summary,
    LOGS_DIR,
    CONFIG_LOG_PATH
)
from utils.logging import get_logger

def validate_config():
    logger = get_logger("config_validation")
    errors = []
    warnings = []

    # Ensure directories exist
    try:
        ensure_dirs()
        logger.info("Directory structure verified.")
    except Exception as e:
        errors.append(f"Failed to create directories: {e}")

    # Validate Seed
    if not isinstance(SEED, int) or SEED < 0:
        errors.append(f"Invalid SEED: {SEED}. Must be a non-negative integer.")
    else:
        logger.info(f"Seed validated: {SEED}")

    # Validate Quantization Levels
    required_levels = {4, 6, 8, 16}
    if set(QUANTIZATION_LEVELS) != required_levels:
        errors.append(f"Invalid QUANTIZATION_LEVELS: {QUANTIZATION_LEVELS}. Expected {required_levels}.")
    else:
        logger.info(f"Quantization levels validated: {QUANTIZATION_LEVELS}")

    # Validate Noise Stds
    if not all(isinstance(x, (int, float)) and x >= 0 for x in NOISE_STDS):
        errors.append(f"Invalid NOISE_STDS: {NOISE_STDS}. All must be non-negative numbers.")
    else:
        logger.info(f"Noise std devs validated: {NOISE_STDS}")

    # Validate Subset Size
    if not isinstance(SUBSET_SIZE, int) or SUBSET_SIZE <= 0:
        errors.append(f"Invalid SUBSET_SIZE: {SUBSET_SIZE}. Must be a positive integer.")
    else:
        logger.info(f"Subset size validated: {SUBSET_SIZE}")

    # Validate Resource Constraints
    if MAX_RAM_GB <= 0:
        errors.append(f"Invalid MAX_RAM_GB: {MAX_RAM_GB}. Must be positive.")
    else:
        logger.info(f"Max RAM validated: {MAX_RAM_GB} GB")

    if MAX_TIME_HOURS <= 0:
        errors.append(f"Invalid MAX_TIME_HOURS: {MAX_TIME_HOURS}. Must be positive.")
    else:
        logger.info(f"Max time validated: {MAX_TIME_HOURS} hours")

    # Validate Horizons
    expected_horizons = {100, 500, 1000}
    if set(INFER_HORIZONS) != expected_horizons:
        errors.append(f"Invalid INFER_HORIZONS: {INFER_HORIZONS}. Expected {expected_horizons}.")
    else:
        logger.info(f"Inference horizons validated: {INFER_HORIZONS}")

    # Get summary and log it
    summary = get_config_summary()
    logger.info(f"Configuration summary generated.")

    # Write validation log
    log_entry = {
        "status": "PASSED" if not errors else "FAILED",
        "errors": errors,
        "warnings": warnings,
        "config_summary": summary
    }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_LOG_PATH, "w") as f:
        json.dump(log_entry, f, indent=2)

    logger.info(f"Validation log written to {CONFIG_LOG_PATH}")

    if errors:
        for err in errors:
            logger.error(err)
        return False
    return True

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
