"""
Data Directory Setup Module for llmXive Project.

This module is responsible for initializing the project's data directory structure
as defined in T009. It creates the raw, processed, and artifacts subdirectories
under the main data/ folder, ensuring the pipeline has a valid filesystem
foundation for storing datasets and outputs.
"""
import os
from pathlib import Path
import sys
import logging

# Add parent directory to path to allow imports from utils if needed
# although this specific task relies on standard library and config constants
# if they were to be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.config import get_paths, ensure_directories

def setup_data_structure():
    """
    Creates the required data directory hierarchy.

    Structure:
    data/
    ├── raw/        (Raw downloaded data, synthetic generators output)
    ├── processed/  (Cleaned, feature-engineered data)
    └── artifacts/  (Model outputs, reports, visualizations)

    Returns:
        dict: A dictionary mapping logical names to absolute Path objects.
    """
    logger = logging.getLogger(__name__)
    
    # Get the base project paths using the existing config module
    paths = get_paths()
    base_data_dir = paths.get('data_dir')
    
    if not base_data_dir:
        # Fallback if config hasn't been fully initialized or paths dict is empty
        # This ensures robustness if get_paths returns None for specific keys
        base_data_dir = Path("data")
        logger.warning("Config 'data_dir' not found, using default 'data' relative path.")
    
    # Define the required subdirectories relative to the base data directory
    subdirs = ['raw', 'processed', 'artifacts']
    
    created_paths = {}
    for subdir in subdirs:
        full_path = base_data_dir / subdir
        created_paths[subdir] = full_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    return created_paths

def main():
    """
    Entry point for the setup_data_dirs script.
    Executes the directory creation and logs the result.
    """
    # Ensure logging is configured
    from utils.logging_config import configure_root_logger
    configure_root_logger()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting data directory setup (T009)...")
    
    try:
        paths = setup_data_structure()
        logger.info("Data directory structure setup complete.")
        logger.info(f"Directories created/verified: {list(paths.keys())}")
        
        # Print absolute paths for verification
        for name, path in paths.items():
            print(f"{name}: {path.resolve()}")
            
        return 0
    except Exception as e:
        logger.error(f"Failed to setup data directories: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())