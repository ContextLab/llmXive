import subprocess
import sys
from pathlib import Path
import logging
from config import setup_logging

logger = setup_logging(__name__)

def run_flake8_check(path: str) -> bool:
    """Run flake8 on a file or directory."""
    try:
        result = subprocess.run(
            ["flake8", path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info(f"Flake8 passed for {path}")
            return True
        else:
            logger.warning(f"Flake8 failed for {path}: {result.stdout}")
            return False
    except Exception as e:
        logger.error(f"Flake8 execution failed: {e}")
        return False

def run_black_format(path: str) -> bool:
    """Run black on a file or directory."""
    try:
        result = subprocess.run(
            ["black", path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info(f"Black formatted {path}")
            return True
        else:
            logger.warning(f"Black failed for {path}: {result.stdout}")
            return False
    except Exception as e:
        logger.error(f"Black execution failed: {e}")
        return False

def run_all_checks(path: str) -> bool:
    """Run all linting checks."""
    flake_ok = run_flake8_check(path)
    black_ok = run_black_format(path)
    return flake_ok and black_ok

def format_code(code: str) -> str:
    """Format code string using black (requires black to be installed)."""
    # This is a placeholder; in practice, you'd use black's API
    # or subprocess to format the string.
    return code