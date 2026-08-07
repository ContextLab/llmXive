"""
Verify that the required data directory structure exists.

This script corresponds to task T008c.
It asserts the existence of 'data/raw/' and 'data/processed/' directories.
"""
import os
import sys
from pathlib import Path
import logging

# Setup basic logging for the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_directory_structure():
    """
    Verify the existence of required data directories.
    
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_raw_path = project_root / 'data' / 'raw'
    data_processed_path = project_root / 'data' / 'processed'

    logger.info(f"Verifying directory structure at: {project_root}")

    try:
        # Requirement: Execute assert os.path.isdir('data/raw')
        logger.info(f"Checking: {data_raw_path}")
        assert os.path.isdir(data_raw_path), f"Directory not found: {data_raw_path}"
        logger.info(f"✓ Verified: {data_raw_path}")

        # Requirement: Execute assert os.path.isdir('data/processed')
        logger.info(f"Checking: {data_processed_path}")
        assert os.path.isdir(data_processed_path), f"Directory not found: {data_processed_path}"
        logger.info(f"✓ Verified: {data_processed_path}")

        logger.info("Directory structure verification PASSED.")
        return True

    except AssertionError as e:
        logger.error(f"Verification FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def main():
    """Entry point for the script."""
    success = verify_directory_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
