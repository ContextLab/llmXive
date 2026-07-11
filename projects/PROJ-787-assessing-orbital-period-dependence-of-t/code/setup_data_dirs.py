import os
import sys
import logging
from pathlib import Path
from utils.logging_config import setup_logging, get_logger
from utils.checksum_utils import initialize_data_directories, save_checksum, verify_checksum

def main():
    """
    Main entry point to initialize the data directory structure.
    
    This script:
    1. Sets up logging
    2. Creates the required directory structure (data/raw, data/processed, data/interim)
    3. Creates an initial .gitkeep file in each directory to ensure they are tracked
    4. Logs the successful creation
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("Starting data directory initialization...")
    
    try:
        # Initialize directories
        directories = initialize_data_directories()
        
        # Create .gitkeep files to ensure directories are tracked by git
        for name, dir_path in directories.items():
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                logger.info(f"Created .gitkeep in {dir_path}")
        
        # Create a manifest file listing the directories
        manifest_path = Path("data") / "MANIFEST.json"
        manifest_data = {
            "version": "1.0",
            "created_by": "setup_data_dirs.py",
            "directories": {name: str(path) for name, path in directories.items()},
            "status": "initialized"
        }
        
        import json
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Data directory structure initialized successfully.")
        logger.info(f"Directories created: {', '.join(directories.keys())}")
        logger.info(f"Manifest saved to: {manifest_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to initialize data directories: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
