"""
Script to create the required directory structure for the project.
This task (T008a) creates 'data/raw/' and 'data/processed/' directories.
"""
import logging
import sys
from pathlib import Path
import logging

# Import project root utility from the existing API surface
from utils.config import get_project_root

def create_directories() -> bool:
    """
    Creates the 'data/raw' and 'data/processed' directories under the project root.
    
    Returns:
        True if directories were created or already exist, False on failure.
    """
    project_root = get_project_root()
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    try:
        # Requirement: Execute os.makedirs with exist_ok=True
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Successfully ensured existence of: {raw_dir}")
        logging.info(f"Successfully ensured existence of: {processed_dir}")
        
        # Verification step as per requirements
        assert raw_dir.is_dir(), f"Failed to create or verify {raw_dir}"
        assert processed_dir.is_dir(), f"Failed to create or verify {processed_dir}"
        
        return True
    except OSError as e:
        logging.error(f"Failed to create directories: {e}")
        return False
    except AssertionError as e:
        logging.error(f"Directory verification failed: {e}")
        return False

def main() -> int:
    """Entry point for the script."""
    configure_root_logger()
    success = create_directories()
    return 0 if success else 1

def configure_root_logger():
    """Basic logging configuration for this script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

if __name__ == "__main__":
    sys.exit(main())
