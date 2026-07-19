"""
Module to create the required data directory structure for the project.

This task (T004a) ensures that the `data/raw` and `data/processed` directories
exist, along with other necessary subdirectories defined in the project plan.
"""
import os
from pathlib import Path
import sys
import logging

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_data_directories(base_path: Optional[Path] = None) -> bool:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root path of the project. Defaults to the current working directory.
        
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the required directory structure relative to the base path
    # Based on T001 requirements and project conventions
    directories = [
        "data/raw",
        "data/processed",
        "state",
        "output",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs/paper",
        "docs/reports",
        # Ensure parent data directories exist (though usually created by subdirs)
        "data",
    ]
    
    success = True
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            else:
                logger.debug(f"Directory already exists: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
        
        # Verify creation
        if not full_path.exists():
            logger.error(f"Verification failed: Directory {full_path} does not exist after creation attempt.")
            success = False
    
    return success

def main():
    """Main entry point for creating data directories."""
    logger.info("Starting directory creation task (T004a)...")
    
    # Determine project root (assuming this script is in code/utils/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    success = create_data_directories(project_root)
    
    if success:
        logger.info("All required directories created successfully.")
        # List the created structure for verification
        data_raw = project_root / "data" / "raw"
        data_processed = project_root / "data" / "processed"
        logger.info(f"Verification: data/raw exists: {data_raw.exists()}")
        logger.info(f"Verification: data/processed exists: {data_processed.exists()}")
    else:
        logger.error("Failed to create one or more directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()