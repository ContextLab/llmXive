"""
Directory Structure Verification Script for llmXive Project.

This script verifies that the required project directory structure exists
and is writable. It creates directories if they do not exist and tests
write permissions by creating and deleting a temporary marker file.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging to capture verification results
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/verification.log')
    ]
)
logger = logging.getLogger(__name__)

# Define the required directory structure relative to project root
REQUIRED_DIRS = [
    "code/data_ingestion",
    "code/modeling",
    "code/reporting",
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "logs",
    "docs"
]

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists and is writable.
    
    Args:
        path: Path object representing the directory to check/create
        
    Returns:
        bool: True if directory exists and is writable, False otherwise
    """
    try:
        # Create directory if it doesn't exist (including parents)
        path.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions by creating a temporary marker file
        marker_file = path / ".write_test_marker"
        try:
            marker_file.touch()
            marker_file.unlink()  # Remove immediately after creation
            logger.info(f"✓ Directory {path} exists and is writable")
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"✗ Directory {path} exists but is NOT writable: {e}")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to verify the entire directory structure.
    
    Returns:
        int: 0 if all directories are verified, 1 if any verification failed
    """
    logger.info("Starting directory structure verification...")
    
    # Ensure logs directory exists first so logging works
    logs_path = Path("logs")
    if not logs_path.exists():
        logs_path.mkdir(parents=True, exist_ok=True)
        logger.info("Created logs directory for verification logging")
    
    all_passed = True
    verified_dirs = []
    failed_dirs = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = Path(dir_path)
        if ensure_directory(full_path):
            verified_dirs.append(dir_path)
        else:
            failed_dirs.append(dir_path)
            all_passed = False
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"Verification Summary:")
    logger.info(f"  Total directories checked: {len(REQUIRED_DIRS)}")
    logger.info(f"  Successfully verified: {len(verified_dirs)}")
    logger.info(f"  Failed verification: {len(failed_dirs)}")
    
    if verified_dirs:
        logger.info("  Verified directories:")
        for d in verified_dirs:
            logger.info(f"    - {d}")
    
    if failed_dirs:
        logger.warning("  Failed directories:")
        for d in failed_dirs:
            logger.warning(f"    - {d}")
    
    logger.info("=" * 50)
    
    if all_passed:
        logger.info("✓ All required directories exist and are writable")
        return 0
    else:
        logger.error("✗ Directory verification failed for some directories")
        return 1

if __name__ == "__main__":
    sys.exit(main())