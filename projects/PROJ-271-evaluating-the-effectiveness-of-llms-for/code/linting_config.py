import subprocess
import sys
from pathlib import Path
import logging
from config import setup_logging

logger = setup_logging(__name__)

def run_flake8_check() -> bool:
    """Run flake8 linter on the code directory.

    Returns:
        bool: True if no issues found, False otherwise.
    """
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir), "--max-line-length=88", "--extend-ignore=E203"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Flake8 check passed.")
            return True
        else:
            logger.warning("Flake8 found issues:\n%s", result.stdout)
            return False
    except Exception as e:
        logger.error("Flake8 check failed: %s", e)
        return False

def run_black_format() -> bool:
    """Run Black formatter on the code directory.

    Returns:
        bool: True if formatting successful, False otherwise.
    """
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--line-length", "88", str(code_dir)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Black formatting completed successfully.")
            return True
        else:
            logger.warning("Black formatting encountered issues:\n%s", result.stderr)
            return False
    except Exception as e:
        logger.error("Black formatting failed: %s", e)
        return False

def format_code() -> bool:
    """Format all Python files in the code directory using Black.

    Returns:
        bool: True if formatting successful, False otherwise.
    """
    logger.info("Starting code formatting with Black...")
    success = run_black_format()
    if success:
        logger.info("Code formatting completed successfully.")
    else:
        logger.error("Code formatting failed.")
    return success

def run_all_checks() -> bool:
    """Run all linting and formatting checks.

    Returns:
        bool: True if all checks passed, False otherwise.
    """
    logger.info("Running all linting and formatting checks...")

    flake8_ok = run_flake8_check()
    black_ok = run_black_format()

    if flake8_ok and black_ok:
        logger.info("All checks passed.")
        return True
    else:
        logger.warning("Some checks failed. Please review the logs.")
        return False

if __name__ == "__main__":
    run_all_checks()