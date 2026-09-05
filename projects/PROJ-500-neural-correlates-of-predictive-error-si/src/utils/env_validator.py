"""
Environment Variable Validation and Error Handling Infrastructure.

This module provides robust validation for critical environment variables
required by the pipeline (DATA_DIR, SEED, RAM_LIMIT). It ensures that
the execution environment is correctly configured before any heavy
processing begins, failing loudly if requirements are not met.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass, field

from .logging import get_logger, log_error, log_event

logger = get_logger(__name__)

@dataclass
class EnvValidationError:
    """Represents a specific validation error for an environment variable."""
    variable_name: str
    message: str
    fatal: bool = True

@dataclass
class ValidationResult:
    """Container for the result of environment validation."""
    is_valid: bool
    errors: List[EnvValidationError] = field(default_factory=list)
    config: dict = field(default_factory=dict)

    def add_error(self, variable: str, message: str, fatal: bool = True):
        self.errors.append(EnvValidationError(variable, message, fatal))
        self.is_valid = False

def validate_data_dir(data_dir_str: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validates the DATA_DIR environment variable.

    Checks:
    1. Variable is set.
    2. Path exists.
    3. Path is a directory.
    4. Path is writable (basic check by trying to create a temp file).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not data_dir_str:
        return False, "DATA_DIR environment variable is not set."

    data_path = Path(data_dir_str)

    if not data_path.exists():
        return False, f"DATA_DIR path does not exist: {data_path}"

    if not data_path.is_dir():
        return False, f"DATA_DIR path is not a directory: {data_path}"

    # Check writability
    try:
        test_file = data_path / ".env_validator_write_test"
        test_file.touch(exist_ok=False)
        test_file.unlink()
    except (OSError, PermissionError) as e:
        return False, f"DATA_DIR is not writable: {data_path}. Error: {e}"

    return True, None

def validate_seed(seed_str: Optional[str]) -> Tuple[bool, Optional[int]]:
    """
    Validates the SEED environment variable.

    Checks:
    1. Variable is set.
    2. Variable is a valid integer.
    3. Value is non-negative (standard for RNG seeds).

    Returns:
        Tuple of (is_valid, parsed_seed).
    """
    if not seed_str:
        return False, None

    try:
        seed_val = int(seed_str)
        if seed_val < 0:
            return False, None, "SEED must be a non-negative integer."
        return True, seed_val, None
    except ValueError:
        return False, None, f"SEED is not a valid integer: {seed_str}"

def validate_ram_limit(ram_limit_str: Optional[str]) -> Tuple[bool, Optional[float]]:
    """
    Validates the RAM_LIMIT environment variable (in GB).

    Checks:
    1. Variable is set.
    2. Variable is a valid float.
    3. Value is positive and reasonable (e.g., > 0.1 GB).

    Returns:
        Tuple of (is_valid, parsed_limit_gb).
    """
    if not ram_limit_str:
        return False, None

    try:
        limit_gb = float(ram_limit_str)
        if limit_gb <= 0:
            return False, None, "RAM_LIMIT must be a positive number."
        if limit_gb < 0.1:
            return False, None, f"RAM_LIMIT ({limit_gb} GB) is unreasonably low."
        return True, limit_gb, None
    except ValueError:
        return False, None, f"RAM_LIMIT is not a valid number: {ram_limit_str}"

def validate_environment() -> ValidationResult:
    """
    Main entry point for validating all critical environment variables.

    This function checks DATA_DIR, SEED, and RAM_LIMIT.
    If any FATAL error is found, it logs the error and returns a failure result.
    The pipeline should halt if validation fails.

    Returns:
        ValidationResult containing status and any errors.
    """
    result = ValidationResult(is_valid=True)

    # 1. Validate DATA_DIR
    data_dir = os.getenv("DATA_DIR")
    is_valid, error_msg = validate_data_dir(data_dir)
    if not is_valid:
        result.add_error("DATA_DIR", error_msg, fatal=True)
        logger.error(f"Environment Validation Failed: DATA_DIR - {error_msg}")
    else:
        result.config["DATA_DIR"] = str(Path(data_dir).resolve())
        logger.info(f"Environment Validation Passed: DATA_DIR = {result.config['DATA_DIR']}")

    # 2. Validate SEED
    seed_str = os.getenv("SEED")
    # Note: validate_seed returns (bool, seed, error_msg) or (bool, None, error_msg)
    # Adjusting signature usage for clarity in this block
    if not seed_str:
        result.add_error("SEED", "SEED environment variable is not set.", fatal=True)
        logger.error("Environment Validation Failed: SEED - Variable not set")
    else:
        try:
            seed_val = int(seed_str)
            if seed_val < 0:
                result.add_error("SEED", "SEED must be a non-negative integer.", fatal=True)
                logger.error(f"Environment Validation Failed: SEED - Invalid value {seed_val}")
            else:
                result.config["SEED"] = seed_val
                logger.info(f"Environment Validation Passed: SEED = {seed_val}")
        except ValueError:
            result.add_error("SEED", f"SEED is not a valid integer: {seed_str}", fatal=True)
            logger.error(f"Environment Validation Failed: SEED - Invalid format {seed_str}")

    # 3. Validate RAM_LIMIT
    ram_limit_str = os.getenv("RAM_LIMIT")
    if not ram_limit_str:
        result.add_error("RAM_LIMIT", "RAM_LIMIT environment variable is not set.", fatal=True)
        logger.error("Environment Validation Failed: RAM_LIMIT - Variable not set")
    else:
        try:
            limit_gb = float(ram_limit_str)
            if limit_gb <= 0:
                result.add_error("RAM_LIMIT", "RAM_LIMIT must be a positive number.", fatal=True)
                logger.error(f"Environment Validation Failed: RAM_LIMIT - Invalid value {limit_gb}")
            else:
                result.config["RAM_LIMIT"] = limit_gb
                logger.info(f"Environment Validation Passed: RAM_LIMIT = {limit_gb} GB")
        except ValueError:
            result.add_error("RAM_LIMIT", f"RAM_LIMIT is not a valid number: {ram_limit_str}", fatal=True)
            logger.error(f"Environment Validation Failed: RAM_LIMIT - Invalid format {ram_limit_str}")

    return result

def get_validated_config() -> dict:
    """
    Convenience function to get the validated configuration.
    Raises RuntimeError if validation fails.
    """
    result = validate_environment()
    if not result.is_valid:
        error_details = "; ".join([f"{e.variable_name}: {e.message}" for e in result.errors])
        raise RuntimeError(f"Environment validation failed: {error_details}")
    return result.config

def main():
    """
    CLI entry point for running validation independently.
    Usage: python -m src.utils.env_validator
    """
    logger.info("Starting environment validation...")
    result = validate_environment()

    if result.is_valid:
        logger.info("Environment validation successful.")
        logger.info(f"Config: {result.config}")
        return 0
    else:
        logger.error("Environment validation FAILED.")
        for err in result.errors:
            logger.error(f"  - {err.variable_name}: {err.message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
