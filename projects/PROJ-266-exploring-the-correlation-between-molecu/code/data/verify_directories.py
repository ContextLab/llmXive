"""
Directory Structure Verification Script for PROJ-266.

This script verifies the existence of the required data directories
(`data/raw` and `data/processed`) as per task T008c.
"""
import os
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_project_root
from utils.logging import get_logger, configure_root_logger

logger = get_logger(__name__)


def verify_directories() -> bool:
    """
    Verify that the required directory structure exists.

    Requirements (T008c):
    - Execute `assert os.path.isdir('data/raw')`
    - Execute `assert os.path.isdir('data/processed')`

    Returns:
        bool: True if all directories exist, False otherwise.

    Raises:
        AssertionError: If any required directory is missing.
    """
    project_root = get_project_root()
    data_raw_path = project_root / "data" / "raw"
    data_processed_path = project_root / "data" / "processed"

    logger.info(f"Verifying directory structure at project root: {project_root}")

    # Requirement: Verify data/raw exists
    logger.info(f"Checking existence of: {data_raw_path}")
    if not os.path.isdir(data_raw_path):
        error_msg = f"Directory missing: {data_raw_path}. Please run T008a first."
        logger.error(error_msg)
        raise AssertionError(error_msg)
    logger.info(f"Verified: {data_raw_path} exists.")

    # Requirement: Verify data/processed exists
    logger.info(f"Checking existence of: {data_processed_path}")
    if not os.path.isdir(data_processed_path):
        error_msg = f"Directory missing: {data_processed_path}. Please run T008a first."
        logger.error(error_msg)
        raise AssertionError(error_msg)
    logger.info(f"Verified: {data_processed_path} exists.")

    logger.info("Directory structure verification successful.")
    return True


def main() -> int:
    """
    Main entry point for the verification script.

    Returns:
        int: 0 on success, 1 on failure.
    """
    configure_root_logger()
    try:
        verify_directories()
        logger.info("T008c Verification: PASSED")
        return 0
    except AssertionError as e:
        logger.error(f"T008c Verification: FAILED - {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())