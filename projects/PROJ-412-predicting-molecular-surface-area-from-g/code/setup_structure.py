import os
import sys
from pathlib import Path
import logging
from utils.logging import get_logger

def create_directories():
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/splits/
    - results/
    
    Also ensures subdirectories for code (data, models, eval, utils) and
    tests (contract, unit, integration) exist as per project structure.
    """
    logger = get_logger(__name__)
    
    # Determine project root (parent of the code/ directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define all required directories relative to project root
    required_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/splits",
        "results/reports",
        "results/plots"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            logger.debug(f"Directory already exists: {full_path}")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
    
    logger.info(f"Directory setup complete: {created_count} created, {skipped_count} already existed")
    return True

def main():
    """Main entry point for directory structure setup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = get_logger(__name__)
    logger.info("Starting directory structure setup...")
    
    try:
        create_directories()
        logger.info("Directory structure setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to setup directory structure: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())