import os
import logging
from pathlib import Path
from config import get_project_root

logger = logging.getLogger(__name__)

def setup_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    Ensures all required folders for code, data, and documentation exist.
    """
    root = get_project_root()
    
    # Define directory paths relative to root
    dirs = [
        # Code structure
        "code/data",
        "code/stimuli",
        "code/analysis",
        "code/viz",
        "code/tests",
        
        # Data structure
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        
        # Documentation
        "docs",
    ]
    
    created_count = 0
    for dir_path in dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Directory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for directory setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    setup_directories()

if __name__ == "__main__":
    main()