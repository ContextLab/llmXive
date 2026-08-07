"""
Script to create the required directory structure for the project.
Implements T008a: Create directory structure for data/raw/ and data/processed/.
"""
import os
import sys
from pathlib import Path
import logging

# Add parent directory to path to allow imports if run as a script
# but primarily this script relies on standard library
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def create_directories() -> bool:
    """
    Create the required directory structure.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Creating directories in project root: {PROJECT_ROOT}")
    
    try:
        # Create data/raw/
        logger.info(f"Creating directory: {RAW_DIR}")
        os.makedirs(RAW_DIR, exist_ok=True)
        
        # Create data/processed/
        logger.info(f"Creating directory: {PROCESSED_DIR}")
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        
        # Verification step as per T008a requirements
        assert os.path.isdir(RAW_DIR), f"Failed to create directory: {RAW_DIR}"
        assert os.path.isdir(PROCESSED_DIR), f"Failed to create directory: {PROCESSED_DIR}"
        
        logger.info("Directory structure created and verified successfully.")
        return True
        
    except AssertionError as e:
        logger.error(f"Verification failed: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error while creating directories: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main() -> int:
    """Main entry point for the script."""
    logger.info("Starting directory creation script (T008a)...")
    
    if create_directories():
        logger.info("T008a completed successfully.")
        return 0
    else:
        logger.error("T008a failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
