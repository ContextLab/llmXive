import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger

def create_directories(logger: logging.Logger):
    """
    Create the required directory structure for the project.
    Creates code/, code/data/, code/models/, code/eval/, code/utils/,
    data/, data/raw/, data/processed/, data/splits/, data/schemas/,
    tests/, tests/contract/, tests/unit/, tests/integration/,
    results/, results/reports/, results/plots/
    """
    # Define all directories relative to project root
    # Assuming project root is the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        # Code structure
        project_root / "code",
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "eval",
        project_root / "code" / "utils",
        
        # Data structure
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "splits",
        project_root / "data" / "schemas",
        
        # Tests structure
        project_root / "tests",
        project_root / "tests" / "contract",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        
        # Results structure
        project_root / "results",
        project_root / "results" / "reports",
        project_root / "results" / "plots",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    logger.info(f"Directory creation complete. Created {created_count} new directories.")
    return created_count

def main():
    """Main entry point for directory setup."""
    logger = get_logger("setup_structure")
    logger.info("Starting directory structure creation...")
    
    try:
        create_directories(logger)
        logger.info("Directory structure setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Error during directory creation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
