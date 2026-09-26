"""
Verification script for .ruff.toml configuration.
Asserts the file exists and contains required keys per T003.
"""
import os
import sys
import tomllib
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

REQUIRED_KEYS = {
    "max-line-length": int,
    "select": list,
    "ignore": list,
}

REQUIRED_SELECT_VALUES = {"E", "F", "W", "I"}
REQUIRED_IGNORE_VALUES = {"E501"}

CONFIG_PATH = Path(".ruff.toml")

def verify_ruff_config() -> bool:
    """
    Verify that .ruff.toml exists and contains the required configuration.

    Returns:
        bool: True if valid, False otherwise.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If required keys or values are missing.
    """
    if not CONFIG_PATH.exists():
        msg = f"Configuration file {CONFIG_PATH} does not exist."
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info(f"Found {CONFIG_PATH}, validating content...")

    try:
        with open(CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        msg = f"Failed to parse {CONFIG_PATH}: {e}"
        logger.error(msg)
        raise ValueError(msg) from e

    # Check for required top-level keys
    missing_keys = []
    for key, expected_type in REQUIRED_KEYS.items():
        if key not in config:
            missing_keys.append(key)
        elif not isinstance(config[key], expected_type):
            msg = f"Key '{key}' exists but is not of type {expected_type.__name__}."
            logger.error(msg)
            raise ValueError(msg)

    if missing_keys:
        msg = f"Missing required keys in {CONFIG_PATH}: {missing_keys}"
        logger.error(msg)
        raise ValueError(msg)

    # Validate 'select' list contains required values
    select_vals = set(config["select"])
    missing_select = REQUIRED_SELECT_VALUES - select_vals
    if missing_select:
        msg = f"Key 'select' missing required values: {missing_select}"
        logger.error(msg)
        raise ValueError(msg)

    # Validate 'ignore' list contains required values
    ignore_vals = set(config["ignore"])
    missing_ignore = REQUIRED_IGNORE_VALUES - ignore_vals
    if missing_ignore:
        msg = f"Key 'ignore' missing required values: {missing_ignore}"
        logger.error(msg)
        raise ValueError(msg)

    logger.info("Validation passed: .ruff.toml is valid and contains all required keys.")
    return True

def create_dummy_file_for_check() -> Path:
    """
    Creates a temporary dummy Python file to run ruff check against.
    Returns the path to the dummy file.
    """
    dummy_path = Path("data/logs/dummy_check.py")
    dummy_path.parent.mkdir(parents=True, exist_ok=True)
    content = """
# Dummy file for ruff verification
import os
import sys

def test_func():
    x=1
    print("Hello")
"""
    with open(dummy_path, "w", encoding="utf-8") as f:
        f.write(content)
    return dummy_path

def main():
    """Main entry point for verification."""
    setup_logging(level=logging.INFO)
    try:
        verify_ruff_config()
        # If config is valid, optionally run a dry check on a dummy file
        # to ensure ruff can actually read the config without crashing.
        dummy_file = create_dummy_file_for_check()
        logger.info(f"Running ruff check on dummy file: {dummy_file}")
        import subprocess
        result = subprocess.run(
            ["ruff", "check", "--config", str(CONFIG_PATH), str(dummy_file)],
            capture_output=True,
            text=True
        )
        # ruff returns 0 if no errors, 1 if errors found (which is fine for config check)
        # We only care that it didn't crash due to config syntax errors.
        if result.returncode == 2:
            msg = f"Ruff failed to parse config: {result.stderr}"
            logger.error(msg)
            sys.exit(1)
        
        logger.info("Ruff check executed successfully against config.")
        print("Verification successful: .ruff.toml exists and is valid.")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during verification")
        print(f"Verification failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()