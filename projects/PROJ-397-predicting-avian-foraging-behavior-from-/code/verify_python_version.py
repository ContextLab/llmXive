"""
verify_python_version.py

Verifies that the current Python environment is version 3.11.x.
Exits with code 0 if the version matches, code 1 otherwise.
"""
import sys
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point to verify Python version.
    Checks if sys.version matches the pattern 3.11.x.
    """
    current_version = sys.version_info
    version_string = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    
    logger.info(f"Detected Python version: {version_string}")

    # Target major.minor version is 3.11
    target_major = 3
    target_minor = 11

    if current_version.major == target_major and current_version.minor == target_minor:
        logger.info(f"SUCCESS: Python version {version_string} matches required 3.11.x.")
        return 0
    else:
        logger.error(f"FAILURE: Python version {version_string} does not match required 3.11.x.")
        logger.error(f"Expected: 3.11.x, Got: {current_version.major}.{current_version.minor}.{current_version.micro}")
        return 1

if __name__ == "__main__":
    sys.exit(main())