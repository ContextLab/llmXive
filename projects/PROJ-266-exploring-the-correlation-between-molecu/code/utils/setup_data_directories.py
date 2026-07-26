import logging
import sys
from pathlib import Path
from typing import List

# Import the function from the setup_project_structure module
import setup_project_structure

def create_directories(root: Path) -> List[Path]:
    """
    Create the data-related directories.
    
    Args:
        root: The project root directory.
        
    Returns:
        A list of created directory paths.
    """
    data_dirs = ["data", "data/raw", "data/processed"]
    created_dirs = []
    
    for dir_path in data_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(full_path)
            logging.info(f"Created directory: {full_path}")
        else:
            logging.info(f"Directory already exists: {full_path}")
            
    return created_dirs

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting data directory creation...")
    root = setup_project_structure.get_project_root()
    logger.info(f"Project root identified as: {root}")
    
    created_dirs = create_directories(root)
    
    if created_dirs:
        logger.info(f"Successfully created {len(created_dirs)} data directories.")
    else:
        logger.info("No new data directories were created.")
        
    logger.info("Data directory creation complete.")

if __name__ == "__main__":
    main()