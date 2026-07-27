"""
Script to run formatting and linting checks as part of the pipeline.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for the formatting run."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for run_formatting."""
    setup_logging()
    logger = logging.getLogger(__name__)

    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    logger.info("Starting linting and formatting checks...")

    # Run Ruff
    logger.info("Running Ruff check...")
    try:
        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            logger.info("Ruff check passed.")
        elif result.returncode == 1:
            logger.warning("Ruff issues found (not fatal):")
            logger.warning(result.stdout)
        else:
            logger.error(f"Ruff check failed with code {result.returncode}: {result.stderr}")
            sys.exit(1)
    except FileNotFoundError:
        logger.error("Ruff not found. Please install it via 'pip install ruff'.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        logger.error("Ruff check timed out.")
        sys.exit(1)

    # Run Black (check only)
    logger.info("Running Black format check...")
    try:
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            logger.info("Black format check passed.")
        elif result.returncode == 1:
            logger.warning("Black formatting issues found (run 'black code/' to fix):")
            logger.warning(result.stdout)
        else:
            logger.error(f"Black check failed with code {result.returncode}: {result.stderr}")
            sys.exit(1)
    except FileNotFoundError:
        logger.error("Black not found. Please install it via 'pip install black'.")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        logger.error("Black check timed out.")
        sys.exit(1)

    logger.info("Linting and formatting checks completed.")

if __name__ == "__main__":
    main()