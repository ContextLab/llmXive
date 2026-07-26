import os
import sys
from pathlib import Path
from typing import List
import logging

from .config import get_data_path

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_data_directories() -> bool:
    """
    Initialize the directory structure for the plant defense allocation pipeline.
    
    Creates the following directories under the project's data root:
    - data/raw: For raw downloaded FASTQ files
    - data/processed: For intermediate and final processed data
    - data/traits: For compiled trait data
    - data/manifests: For metadata manifests
    - data/synthetic: For synthetic/prototype data
    
    Returns:
        bool: True if all directories were created successfully and are writable,
              False otherwise.
    """
    data_root = get_data_path()
    logger.info(f"Setting up directory structure at: {data_root}")
    
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "traits",
        data_root / "manifests",
        data_root / "synthetic"
    ]
    
    # Create directories
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/Verified directory: {dir_path}")
            
            # Verify writability
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            logger.debug(f"Verified writability for: {dir_path}")
            
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {dir_path}: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error creating directory {dir_path}: {e}")
            return False
    
    # Create flag file to indicate successful setup
    flag_file = data_root / ".dir_setup_complete"
    try:
        with open(flag_file, 'w') as f:
            f.write("Directory setup completed successfully.\n")
            f.write(f"Timestamp: {os.popen('date').read().strip()}\n")
        logger.info(f"Created flag file: {flag_file}")
    except OSError as e:
        logger.error(f"Failed to create flag file {flag_file}: {e}")
        return False
    
    return True

def main() -> int:
    """
    CLI entry point for directory setup.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    success = setup_data_directories()
    if success:
        logger.info("Directory setup completed successfully.")
        return 0
    else:
        logger.error("Directory setup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
