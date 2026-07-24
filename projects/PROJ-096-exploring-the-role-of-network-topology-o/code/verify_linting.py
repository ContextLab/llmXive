"""
Verify linting configuration by running black --check and flake8.

This script ensures that the project codebase adheres to the defined
linting standards (Black formatting and Flake8 rules).

It serves as the single source of truth for lint verification.
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

def run_command(command: list[str], description: str) -> bool:
    """
    Run a shell command and return True if it succeeds.

    Args:
        command: List of command arguments.
        description: Human-readable description of the command.

    Returns:
        True if the command executed successfully (exit code 0), False otherwise.
    """
    logger.info(f"Running {description}...")
    logger.info(f"Command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent.parent,  # Run from project root
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"{description} passed successfully.")
            if result.stdout:
                logger.debug(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"{description} failed.")
            if result.stdout:
                logger.error(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.error(f"STDERR:\n{result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"{description} timed out.")
        return False
    except FileNotFoundError as e:
        logger.error(f"Command not found: {e}. Ensure tools are installed.")
        return False
    except Exception as e:
        logger.error(f"Error running {description}: {e}")
        return False

def main() -> int:
    """
    Main entry point for lint verification.

    Runs black --check and flake8. Returns 0 if all checks pass, 1 otherwise.
    """
    logger.info("Starting lint verification...")

    # Check if we are in the correct project structure
    project_root = Path(__file__).parent.parent
    if not (project_root / "requirements.txt").exists():
        logger.error("Could not find requirements.txt. Are you running from the project root?")
        return 1

    # Run Black check
    black_success = run_command(
        ["black", "--check", "."],
        "Black format check"
    )

    # Run Flake8
    flake8_success = run_command(
        ["flake8", "."],
        "Flake8 lint check"
    )

    if black_success and flake8_success:
        logger.info("All linting checks passed.")
        return 0
    else:
        logger.error("Linting checks failed. Please fix the reported issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())