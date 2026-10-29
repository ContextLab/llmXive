"""
T004: Verify Python 3.11 project setup and package installation.

This script checks that the project's `requirements.txt` can be installed
and that the `requests` package (declared in the requirements) can be
imported without error.  All outcomes are written to
`logs/setup_verification.log` using the project's `paths` helper for
location‑independent logging.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

# Project‑level helpers
from llmxive_toolkit import paths, get_logger

# Resolve the path to the root‑level requirements.txt.
# The script resides in <project_root>/code/, so we need to go up one level.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

log_file = paths.logs("setup_verification.log")
logger = get_logger(__name__, log_file=str(log_file))

def install_requirements() -> bool:
    """
    Install the root‑level requirements.txt using pip.
    Returns True on success, False otherwise.
    """
    logger.info(f"Installing requirements from {REQUIREMENTS_PATH}")
    if not REQUIREMENTS_PATH.is_file():
        logger.error(f"requirements.txt not found at {REQUIREMENTS_PATH}")
        return False
    try:
        # Use the same Python executable that runs this script
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Requirements installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"pip install failed: {e}")
        return False

def verify_import(package_name: str) -> bool:
    """
    Attempt to import ``package_name`` using importlib.
    Returns True if import succeeds, False otherwise.
    """
    logger.info(f"Verifying import of package '{package_name}'")
    try:
        importlib.import_module(package_name)
        logger.info(f"Import of '{package_name}' succeeded.")
        return True
    except ImportError as e:
        logger.error(f"ImportError for '{package_name}': {e}")
        return False

def main() -> None:
    # Step 1: (re)install requirements – idempotent if already satisfied
    if not install_requirements():
        logger.error("Cannot continue verification because requirements failed to install.")
        sys.exit(1)

    # Step 2: Verify that the 'requests' package can be imported
    if verify_import("requests"):
        logger.info("Setup verification completed successfully.")
        sys.exit(0)
    else:
        logger.error("Setup verification failed: 'requests' could not be imported.")
        sys.exit(1)

if __name__ == "__main__":
    main()