"""
Linting and formatting configuration helpers.
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_flake8() -> bool:
    """Runs flake8."""
    try:
        result = subprocess.run([sys.executable, '-m', 'flake8', 'code/'], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        logger.error("Flake8 failed.")
        return False

def run_black() -> bool:
    """Runs black."""
    try:
        result = subprocess.run([sys.executable, '-m', 'black', '--check', 'code/'], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        logger.error("Black check failed.")
        return False

def run_isort() -> bool:
    """Runs isort."""
    try:
        result = subprocess.run([sys.executable, '-m', 'isort', '--check-only', 'code/'], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        logger.error("Isort check failed.")
        return False

def run_all_checks() -> bool:
    """Runs all linting checks."""
    checks = [run_flake8, run_black, run_isort]
    results = [check() for check in checks]
    return all(results)

def run_all_formatters() -> None:
    """Runs formatters to fix issues."""
    subprocess.run([sys.executable, '-m', 'black', 'code/'])
    subprocess.run([sys.executable, '-m', 'isort', 'code/'])

def main():
    """Main entry point."""
    if run_all_checks():
        logger.info("All linting checks passed.")
    else:
        logger.error("Linting checks failed. Run formatters to fix.")

if __name__ == '__main__':
    main()
