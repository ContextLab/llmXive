"""
Script to create and verify the data/processed/ directory.
Ensures idempotency: creates the directory if it does not exist,
and verifies it is writable.
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_dirs
from utils.logger import get_logger
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)

PROCESSED_DIR_NAME = "data/processed"


def ensure_dir_with_backoff(dir_path: Path, retries: int = 3) -> bool:
    """
    Ensures a directory exists. Attempts creation with a simple retry mechanism
    in case of transient file system locks.

    Args:
        dir_path: Path object representing the directory to create.
        retries: Number of attempts to create the directory.

    Returns:
        True if directory exists and is writable, False otherwise.
    """
    for attempt in range(retries):
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Verify writability
            test_file = dir_path / ".write_test"
            try:
                test_file.touch(exist_ok=True)
                test_file.unlink()
                logger.info(f"Directory '{dir_path}' verified as writable.")
                return True
            except OSError as e:
                logger.error(f"Directory '{dir_path}' exists but is not writable: {e}")
                return False
        except OSError as e:
            logger.warning(f"Attempt {attempt + 1} to create '{dir_path}' failed: {e}")
            if attempt == retries - 1:
                logger.error(f"Failed to create directory '{dir_path}' after {retries} attempts.")
                return False
    return False


def setup_processed_dirs() -> bool:
    """
    Main logic to set up the processed data directory.

    Returns:
        True if successful, False if verification fails.
    """
    processed_path = PROJECT_ROOT / PROCESSED_DIR_NAME

    logger.info(f"Ensuring directory exists: {processed_path}")

    if not ensure_dir_with_backoff(processed_path):
        raise ConfigurationError(
            f"ERR_SETUP_001: Failed to create or verify writability of '{processed_path}'."
        )

    logger.info(f"Successfully ensured directory '{processed_path}' exists and is writable.")
    return True


def main():
    """
    Entry point for CLI execution.
    """
    parser = argparse.ArgumentParser(
        description="Create and verify the data/processed/ directory."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of the directory (removes existing content first)."
    )
    args = parser.parse_args()

    try:
        if args.force:
            processed_path = PROJECT_ROOT / PROCESSED_DIR_NAME
            if processed_path.exists():
                logger.info(f"Force removing existing directory: {processed_path}")
                import shutil
                shutil.rmtree(processed_path)

        success = setup_processed_dirs()
        if success:
            print(f"SUCCESS: Directory '{PROCESSED_DIR_NAME}' is ready.")
            sys.exit(0)
        else:
            print(f"FAILURE: Directory '{PROCESSED_DIR_NAME}' verification failed.")
            sys.exit(1)

    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during setup: {e}")
        print(f"ERROR: Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
