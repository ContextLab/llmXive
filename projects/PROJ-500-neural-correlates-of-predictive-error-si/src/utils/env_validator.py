"""
Environment variable validation and error handling infrastructure.

This module provides strict validation for critical environment variables
required by the pipeline, ensuring fail-fast behavior on misconfiguration.
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

# Import logging utilities from the existing sibling module
from .logging import get_logger, log_error, log_event

logger = get_logger(__name__)


@dataclass
class EnvVarDefinition:
    """Definition of a required environment variable."""
    name: str
    description: str
    required: bool = True
    validator: Optional[str] = None  # e.g., 'exists_dir', 'exists_file', 'int_gt_0'
    default: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of an environment validation run."""
    success: bool
    errors: List[str]
    warnings: List[str]
    config: Dict[str, Any]

# Required environment variables for this project
REQUIRED_ENV_VARS = [
    EnvVarDefinition(
        name="DATA_DIR",
        description="Root directory for data storage (raw, interim, processed)",
        required=True,
        validator="exists_dir"
    ),
    EnvVarDefinition(
        name="SEED",
        description="Random seed for reproducibility",
        required=True,
        validator="int_gt_0"
    ),
    EnvVarDefinition(
        name="RAM_LIMIT",
        description="Maximum RAM usage in GB (streaming buffer limit)",
        required=True,
        validator="float_gt_0"
    ),
    EnvVarDefinition(
        name="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
        required=False,
        default="INFO"
    )
]


def validate_env_var(var_def: EnvVarDefinition) -> Tuple[bool, Optional[str], Any]:
    """
    Validate a single environment variable.

    Args:
        var_def: The environment variable definition.

    Returns:
        Tuple of (is_valid, error_message, value)
    """
    value = os.getenv(var_def.name)

    # Check if missing
    if value is None:
        if var_def.required:
            return False, f"Missing required environment variable: {var_def.name}", None
        else:
            return True, None, var_def.default

    # Type and format validation
    try:
        if var_def.validator == "int_gt_0":
            int_val = int(value)
            if int_val <= 0:
                return False, f"{var_def.name} must be an integer > 0, got {value}", None
            return True, None, int_val

        elif var_def.validator == "float_gt_0":
            float_val = float(value)
            if float_val <= 0:
                return False, f"{var_def.name} must be a float > 0, got {value}", None
            return True, None, float_val

        elif var_def.validator == "exists_dir":
            path = Path(value)
            if not path.exists():
                return False, f"{var_def.name} path does not exist: {value}", None
            if not path.is_dir():
                return False, f"{var_def.name} path is not a directory: {value}", None
            return True, None, str(path.resolve())

        elif var_def.validator == "exists_file":
            path = Path(value)
            if not path.exists():
                return False, f"{var_def.name} path does not exist: {value}", None
            if not path.is_file():
                return False, f"{var_def.name} path is not a file: {value}", None
            return True, None, str(path.resolve())

        else:
            # No specific validator, just check presence
            return True, None, value

    except ValueError as e:
        return False, f"Invalid format for {var_def.name}: {value} ({e})", None


def validate_environment() -> ValidationResult:
    """
    Validate all required environment variables.

    Returns:
        ValidationResult with success status, errors, warnings, and parsed config.
    """
    errors: List[str] = []
    warnings: List[str] = []
    config: Dict[str, Any] = {}
    all_valid = True

    log_event("ENV_VALIDATION_START", "Starting environment variable validation")

    for var_def in REQUIRED_ENV_VARS:
        is_valid, error_msg, value = validate_env_var(var_def)

        if not is_valid:
            errors.append(error_msg)
            all_valid = False
            log_error(f"Environment validation failed: {error_msg}")
        else:
            config[var_def.name] = value
            if var_def.required:
                logger.debug(f"Validated required env var: {var_def.name}")
            else:
                logger.debug(f"Using default for optional env var: {var_def.name}={value}")

    if all_valid:
        log_event("ENV_VALIDATION_SUCCESS", "All environment variables validated successfully")
    else:
        log_error(f"Environment validation failed with {len(errors)} errors")

    return ValidationResult(
        success=all_valid,
        errors=errors,
        warnings=warnings,
        config=config
    )


def get_env_config() -> Dict[str, Any]:
    """
    Get validated environment configuration.

    Raises:
        RuntimeError: If environment validation fails.

    Returns:
        Dictionary of validated environment variables.
    """
    result = validate_environment()

    if not result.success:
        error_summary = "; ".join(result.errors)
        raise RuntimeError(f"Environment validation failed: {error_summary}")

    return result.config


def check_env_var_exists(name: str, required: bool = True) -> Optional[str]:
    """
    Check if a specific environment variable exists.

    Args:
        name: Name of the environment variable.
        required: Whether it's required (fail if missing).

    Returns:
        Value if exists, None otherwise.

    Raises:
        RuntimeError: If required variable is missing.
    """
    value = os.getenv(name)
    if value is None and required:
        raise RuntimeError(f"Required environment variable '{name}' is not set")
    return value


def main():
    """
    CLI entry point for environment validation.
    Prints validation results and exits with appropriate code.
    """
    print("Running environment validation...")
    result = validate_environment()

    if result.success:
        print("✓ Environment validation successful")
        print(f"  DATA_DIR: {result.config.get('DATA_DIR')}")
        print(f"  SEED: {result.config.get('SEED')}")
        print(f"  RAM_LIMIT: {result.config.get('RAM_LIMIT')} GB")
        print(f"  LOG_LEVEL: {result.config.get('LOG_LEVEL', 'INFO')}")
        sys.exit(0)
    else:
        print("✗ Environment validation failed")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
