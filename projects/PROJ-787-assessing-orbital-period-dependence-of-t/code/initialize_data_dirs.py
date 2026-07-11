import os
import sys
from pathlib import Path
import logging
from utils.logging_config import setup_logging, get_logger
from utils.setup_dirs import initialize_directories

def main():
    """
    Initialize data directories: Create `data/raw/`, `data/processed/` directories.
    This script ensures the required directory structure exists for the pipeline.
    """
    # Setup logging
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    logger = setup_logging(
        log_file=log_path / "initialize_data_dirs.log",
        module_name="initialize_data_dirs"
    )

    logger.info("Starting data directory initialization for T001b")

    # Define the required data directories relative to the project root
    # Assuming this script is run from the project root or code/ directory
    # We resolve the project root as the parent of 'code' if we are in 'code'
    current_file = Path(__file__).resolve()
    if current_file.name == "__main__.py" or current_file.stem == "initialize_data_dirs":
        # If running directly, assume project root is parent of code/
        project_root = current_file.parent
    else:
        project_root = current_file.parent.parent

    data_root = project_root / "data"

    required_dirs = [
        data_root / "raw",
        data_root / "processed"
    ]

    logger.info(f"Project root identified as: {project_root}")
    logger.info(f"Data root identified as: {data_root}")

    success = True
    for dir_path in required_dirs:
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.info(f"Directory already exists: {dir_path}")
            
            # Verify it is a directory and writable
            if not dir_path.is_dir():
                logger.error(f"Path exists but is not a directory: {dir_path}")
                success = False
            else:
                # Try to create a temporary file to test write permissions
                test_file = dir_path / ".write_test"
                test_file.touch()
                test_file.unlink()
                logger.debug(f"Write permission verified for: {dir_path}")
                
        except PermissionError:
            logger.error(f"Permission denied creating directory: {dir_path}")
            success = False
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False

    if success:
        logger.info("Data directory initialization completed successfully.")
        print("Data directories initialized: data/raw/, data/processed/")
        return 0
    else:
        logger.error("Data directory initialization failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
