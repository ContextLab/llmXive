"""
Verify that .env.example exists and contains required keys.

This script asserts that the .env.example file exists in the project root
and contains the mandatory environment variables:
- VISUAL_GENOME_URL
- SURVEY_API_KEY

It exits with code 0 on success, or code 1 on failure.
"""
import os
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_KEYS = [
    "VISUAL_GENOME_URL",
    "SURVEY_API_KEY"
]

def verify_env_example() -> bool:
    """
    Verify .env.example exists and contains required keys.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    env_example_path = project_root / ".env.example"

    # Check if file exists
    if not env_example_path.exists():
        logger.error(f"File not found: {env_example_path}")
        logger.error("The .env.example file is missing from the project root.")
        return False

    logger.info(f"Found .env.example at: {env_example_path}")

    # Read file contents
    try:
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read .env.example: {e}")
        return False

    # Check for required keys
    missing_keys = []
    for key in REQUIRED_KEYS:
        # Check for key presence (handle both KEY= and KEY=value formats)
        # We look for the key at the start of a line or after whitespace
        # to avoid matching partial keys
        if not any(
            line.strip().startswith(f"{key}=") or line.strip().startswith(f"{key} ")
            for line in content.splitlines()
        ):
            missing_keys.append(key)

    if missing_keys:
        logger.error(f"Missing required keys in .env.example: {missing_keys}")
        logger.error(f"Required keys: {REQUIRED_KEYS}")
        return False

    logger.info("All required keys found in .env.example")
    logger.info(f"Verified keys: {REQUIRED_KEYS}")
    return True

def main() -> None:
    """Main entry point for the verification script."""
    logger.info("Starting .env.example verification...")

    success = verify_env_example()

    if success:
        logger.info("Verification PASSED: .env.example is valid.")
        sys.exit(0)
    else:
        logger.error("Verification FAILED: .env.example is invalid or missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()