"""
Script to configure and verify linting and formatting tools.
This script ensures ruff and black are installed and can be run
to check/format the codebase.
"""
import subprocess
import sys
from pathlib import Path

from config_linting import (
    run_ruff_check,
    run_ruff_fix,
    run_black_check,
    run_black_format,
    run_lint_and_format,
)
from utils import get_logger

logger = get_logger(__name__)


def main():
    """
    Main entry point to configure and run linting/formatting.
    This script:
    1. Checks if ruff and black are installed.
    2. Runs ruff check and black check.
    3. If issues are found, it offers to fix them (or auto-fixes in CI context).
    """
    logger.info("Starting linting and formatting configuration...")

    # Ensure tools are available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "show", "ruff"])
        subprocess.check_call([sys.executable, "-m", "pip", "show", "black"])
        logger.info("Linting tools (ruff, black) are installed.")
    except subprocess.CalledProcessError:
        logger.error("Linting tools not found. Please install them via: pip install ruff black")
        sys.exit(1)

    # Run checks
    logger.info("Running ruff check...")
    ruff_ok = run_ruff_check()
    
    logger.info("Running black check...")
    black_ok = run_black_check()

    if not ruff_ok or not black_ok:
        logger.warning("Issues found. Attempting to fix automatically...")
        run_ruff_fix()
        run_black_format()
        
        # Re-check after fixing
        logger.info("Re-running checks after fixes...")
        ruff_ok = run_ruff_check()
        black_ok = run_black_check()

        if not ruff_ok or not black_ok:
            logger.error("Automatic fixes did not resolve all issues. Please review manually.")
            sys.exit(1)
    
    logger.info("Linting and formatting checks passed.")


if __name__ == "__main__":
    main()
