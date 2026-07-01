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

def create_directories():
    """
    Create the required subdirectories for the project structure.
    
    Creates:
    - code/data/
    - code/models/
    - code/analysis/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    # Define the subdirectories to create
    subdirectories = [
        "data",
        "models",
        "analysis"
    ]
    
    success = True
    
    for subdir_name in subdirectories:
        subdir_path = code_dir / subdir_name
        
        try:
            if not subdir_path.exists():
                subdir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {subdir_path}")
            else:
                logger.info(f"Directory already exists: {subdir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {subdir_path}: {e}")
            success = False
    
    return success

def main():
    """Main entry point for directory creation."""
    logger.info("Starting directory creation for PROJ-224...")
    
    if create_directories():
        logger.info("All required directories created successfully.")
        return 0
    else:
        logger.error("Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
