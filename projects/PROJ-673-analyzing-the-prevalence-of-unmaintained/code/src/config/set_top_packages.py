"""
Configuration script to set the DEFAULT TOP_PACKAGES count for adaptive sampling.

This script sets the environment variable TOP_PACKAGES to 100 as a default value.
It does NOT hardcode this value in the application logic; instead, it ensures
the environment has a sensible default that can be overridden via CLI arguments
in T019 (collect_data.py).

Adheres to Constitution Principle: No hardcoded values in logic.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_TOP_PACKAGES = 100
ENV_VAR_NAME = "TOP_PACKAGES"
ENV_FILE_PATH = Path(__file__).parent.parent.parent / ".env"

def set_default_top_packages(value: int = DEFAULT_TOP_PACKAGES) -> None:
    """
    Sets the TOP_PACKAGES environment variable to the specified value.
    
    Args:
        value: The default number of top packages to analyze.
    """
    logger.info(f"Setting {ENV_VAR_NAME}={value}")
    os.environ[ENV_VAR_NAME] = str(value)
    
    # Update the .env file for persistence across sessions
    update_env_file(value)
    
    logger.info(f"Successfully set {ENV_VAR_NAME} to {value}")

def update_env_file(value: int) -> None:
    """
    Updates the .env file with the new TOP_PACKAGES value.
    
    If the file doesn't exist, it creates it.
    If the key exists, it updates the value.
    If the key doesn't exist, it appends it.
    """
    if not ENV_FILE_PATH.exists():
        logger.info(f"Creating new .env file at {ENV_FILE_PATH}")
        ENV_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(f"# Project Configuration\n")
            f.write(f"# Set by set_top_packages.py\n")
            f.write(f"{ENV_VAR_NAME}={value}\n")
        return

    lines = []
    found = False
    with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{ENV_VAR_NAME}="):
            new_lines.append(f"{ENV_VAR_NAME}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        logger.info(f"Appending {ENV_VAR_NAME}={value} to .env file")
        new_lines.append(f"\n{ENV_VAR_NAME}={value}\n")
    else:
        logger.info(f"Updated {ENV_VAR_NAME} in .env file")

    with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def verify_setting() -> bool:
    """
    Verifies that the TOP_PACKAGES environment variable is set correctly.
    
    Returns:
        True if the value is set to the expected default, False otherwise.
    """
    current_value = os.getenv(ENV_VAR_NAME)
    expected_value = str(DEFAULT_TOP_PACKAGES)
    
    if current_value == expected_value:
        logger.info(f"Verification passed: {ENV_VAR_NAME}={current_value}")
        return True
    else:
        logger.error(f"Verification failed: Expected {expected_value}, got {current_value}")
        return False

def main():
    """
    Main entry point for the script.
    """
    logger.info("Starting set_top_packages.py")
    
    # Set the default value
    set_default_top_packages(DEFAULT_TOP_PACKAGES)
    
    # Verify the setting
    if verify_setting():
        logger.info("Task T017a completed successfully.")
        print(f"SUCCESS: {ENV_VAR_NAME} is set to {DEFAULT_TOP_PACKAGES} as default.")
        print("This value can be overridden via CLI arguments in T019 (collect_data.py).")
        sys.exit(0)
    else:
        logger.error("Failed to set TOP_PACKAGES correctly.")
        sys.exit(1)

if __name__ == "__main__":
    main()
