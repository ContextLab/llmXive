"""
Verify linting configuration by running black and flake8.

This script executes the linting checks defined in the project setup:
- black --check .
- flake8 .

It exits with code 0 if all checks pass, or non-zero if any check fails.
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command: list, description: str) -> bool:
    """
    Run a shell command and return True if it succeeds.

    Args:
        command: List of command arguments
        description: Human-readable description of the command

    Returns:
        True if command exits with code 0, False otherwise
    """
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"✓ {description} passed")
            return True
        else:
            logger.error(f"✗ {description} failed")
            if result.stdout:
                logger.error(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.error(f"STDERR:\n{result.stderr}")
            return False

    except FileNotFoundError:
        logger.error(f"✗ {description} failed: Command not found")
        logger.error("Ensure black and flake8 are installed in the environment")
        return False
    except Exception as e:
        logger.error(f"✗ {description} failed with exception: {e}")
        return False

def main():
    """
    Main function to run all linting checks.
    """
    logger.info("=" * 60)
    logger.info("Starting Linting Verification (Task T003b)")
    logger.info("=" * 60)

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    logger.info(f"Working directory: {project_root}")

    # Define linting commands
    checks = [
        (["black", "--check", "."], "Black code formatting check"),
        (["flake8", "."], "Flake8 linting check"),
    ]

    # Run all checks
    all_passed = True
    for command, description in checks:
        if not run_command(command, description):
            all_passed = False

    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ All linting checks passed successfully")
        logger.info("Task T003b: VERIFIED")
        return 0
    else:
        logger.error("✗ Some linting checks failed")
        logger.error("Task T003b: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())