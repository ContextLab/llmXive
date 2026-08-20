import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_flake8() -> None:
    """Run flake8 linter."""
    logger.info("Running flake8...")
    try:
        result = subprocess.run(['flake8', 'code/'], check=True, capture_output=True, text=True)
        logger.info("Flake8 passed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Flake8 failed:\n{e.stdout}")
        raise

def run_black() -> None:
    """Run black formatter."""
    logger.info("Running black...")
    try:
        subprocess.run(['black', 'code/'], check=True, capture_output=True, text=True)
        logger.info("Black passed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Black failed:\n{e.stdout}")
        raise

def run_isort() -> None:
    """Run isort."""
    logger.info("Running isort...")
    try:
        subprocess.run(['isort', 'code/'], check=True, capture_output=True, text=True)
        logger.info("Isort passed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Isort failed:\n{e.stdout}")
        raise

def run_all_checks() -> None:
    """Run all linters."""
    run_flake8()
    # isort and black are formatters, but we can run them as checks if needed
    # run_isort() 

def run_all_formatters() -> None:
    """Run all formatters."""
    run_black()
    run_isort()

def main() -> None:
    """Main entry point for linting."""
    run_all_checks()
    run_all_formatters()
    logger.info("All linting and formatting checks completed.")

if __name__ == "__main__":
    main()
