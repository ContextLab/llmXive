import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes this script is located at code/setup_directory_structure.py
    """
    current_file = Path(__file__).resolve()
    # Go up two levels: code/setup_directory_structure.py -> code -> root
    return current_file.parent.parent

def create_directories(project_root: Path) -> bool:
    """
    Create the required directory structure for the llmXive project.
    
    Structure:
    code/
      data_generation/
      model_training/
      simulation/
      analysis/
    data/
      raw/
      processed/
      models/
      simulation/
    tests/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define directory paths relative to project root
    directories = [
        # Code modules
        project_root / "code" / "data_generation",
        project_root / "code" / "model_training",
        project_root / "code" / "simulation",
        project_root / "code" / "analysis",
        
        # Data storage
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "models",
        project_root / "data" / "simulation",
        
        # Tests
        project_root / "tests",
        
        # Additional required directories based on task dependencies
        project_root / "data" / "analysis",
        project_root / "state" / "projects",
    ]
    
    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            success = False
    
    return success

def verify_structure(project_root: Path) -> bool:
    """
    Verify that the required directory structure exists.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        bool: True if all required directories exist, False otherwise.
    """
    required_dirs = [
        "code",
        "code/data_generation",
        "code/model_training",
        "code/simulation",
        "code/analysis",
        "data",
        "data/raw",
        "data/processed",
        "data/models",
        "data/simulation",
        "data/analysis",
        "tests",
        "state/projects",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        else:
            logger.info(f"Verified directory: {full_path}")
    
    return all_exist

def main():
    """
    Main entry point for directory structure initialization.
    
    This function:
    1. Determines the project root
    2. Creates all required directories
    3. Verifies the structure was created correctly
    
    Exit codes:
        0: Success
        1: Failure
    """
    logger.info("Starting directory structure initialization...")
    
    try:
        project_root = get_project_root()
        logger.info(f"Project root identified: {project_root}")
        
        # Create directories
        if not create_directories(project_root):
            logger.error("Failed to create some directories")
            sys.exit(1)
        
        # Verify structure
        if not verify_structure(project_root):
            logger.error("Directory structure verification failed")
            sys.exit(1)
        
        logger.info("Directory structure initialization completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
