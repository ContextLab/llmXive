import os
import sys
from pathlib import Path
from utils.logger import get_logger

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    This includes raw, intermediate, and processed data folders,
    as well as specific subdirectories for human and LLM samples.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    logger = get_logger(__name__)
    project_root = Path.cwd()
    
    # Define the relative paths required by the task
    data_dirs = [
        "data/raw/human_samples",
        "data/raw/llm_samples",
        "data/intermediate",
        "data/processed"
    ]
    
    success = True
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
    
    if success:
        logger.info("Data directory structure setup complete.")
    else:
        logger.warning("Some directories could not be created. Check logs for details.")
        
    return success

def main():
    """
    Entry point for the script.
    """
    # Ensure we are running from the project root or code directory
    # If running from code/, we need to adjust path resolution if necessary
    # but mkdir parents=True handles relative paths from cwd generally.
    # However, to be robust, we assume the script is run as `python code/01_setup_data_dirs.py`
    # from the repo root.
    
    if not setup_data_directories():
        sys.exit(1)

if __name__ == "__main__":
    main()