import os
from pathlib import Path
import sys
import logging
from utils.config import get_paths, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_data_structure(base_dir: Path = None) -> bool:
    """
    Creates the required directory structure for data management:
    - data/raw/
    - data/processed/
    - data/artifacts/
    
    Args:
        base_dir: Optional base directory. If None, uses the project root from utils.config.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    try:
        if base_dir is None:
            # Get paths from the config module which handles project root detection
            paths = get_paths()
            base_dir = paths.get("project_root", Path.cwd())
        
        # Define the data directory structure
        data_root = base_dir / "data"
        sub_dirs = ["raw", "processed", "artifacts"]
        
        logger.info(f"Setting up data directory structure at: {data_root}")
        
        # Create the data root if it doesn't exist
        if not data_root.exists():
            data_root.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created data root directory: {data_root}")
        
        # Create subdirectories
        created_count = 0
        for sub_dir in sub_dirs:
            target_path = data_root / sub_dir
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created subdirectory: {target_path}")
                created_count += 1
            else:
                logger.debug(f"Subdirectory already exists: {target_path}")
        
        logger.info(f"Data structure setup complete. Created {created_count} new directories.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup data directory structure: {e}", exc_info=True)
        return False

def main():
    """Entry point for running the data directory setup as a script."""
    logger.info("Starting data directory setup script...")
    success = setup_data_structure()
    if success:
        logger.info("Data directory structure setup successful.")
        sys.exit(0)
    else:
        logger.error("Data directory structure setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
