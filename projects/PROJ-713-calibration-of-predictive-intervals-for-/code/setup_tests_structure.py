"""
Setup script to create and verify the 'tests/' project directory.
Ensures idempotency (creates if not exists) and verifies writability.
"""
import os
import sys
import argparse
from pathlib import Path
from utils.logger import get_logger

# Import project root and config logic if available, otherwise define locally
try:
    from config import PROJECT_ROOT
except ImportError:
    # Fallback if config.py is not yet fully loaded or in a different context
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = get_logger(__name__)


def ensure_dir(path: Path) -> bool:
    """
    Ensure the directory exists. If it does not, create it.
    Returns True if successful, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except PermissionError:
        logger.error(f"Permission denied creating directory: {path}")
        return False
    except OSError as e:
        logger.error(f"OS error creating directory {path}: {e}")
        return False


def verify_writable(path: Path) -> bool:
    """
    Verify that the directory is writable by attempting to create a temporary file.
    Returns True if writable, False otherwise.
    """
    test_file = path / ".write_test_001b.tmp"
    try:
        # Create a temporary file
        test_file.touch()
        # Try to write a small amount of data
        with open(test_file, 'w') as f:
            f.write("test")
        # Remove the test file
        test_file.unlink()
        logger.info(f"Directory is writable: {path}")
        return True
    except PermissionError:
        logger.error(f"Permission denied writing to directory: {path}")
        return False
    except OSError as e:
        logger.error(f"OS error writing to directory {path}: {e}")
        return False


def main(args=None):
    """
    Main entry point for the setup script.
    Creates the 'tests/' directory and verifies it is writable.
    """
    parser = argparse.ArgumentParser(description="Setup tests directory")
    parser.add_argument(
        "--path",
        type=str,
        default="tests",
        help="Relative path to the tests directory (default: tests)"
    )
    parsed_args = parser.parse_args(args)

    target_path = PROJECT_ROOT / parsed_args.path

    logger.info(f"Starting setup for tests directory: {target_path}")

    # Ensure directory exists (Idempotent)
    if not ensure_dir(target_path):
        logger.error("Failed to create tests directory.")
        sys.exit(1)

    # Verify writability
    if not verify_writable(target_path):
        logger.error("Tests directory exists but is not writable.")
        sys.exit(1)

    logger.info(f"Task T001b completed successfully: {target_path} exists and is writable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
