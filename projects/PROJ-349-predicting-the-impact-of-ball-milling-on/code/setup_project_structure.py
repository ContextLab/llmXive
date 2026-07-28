import os
import sys
from pathlib import Path
import logging

# Configure logging for the setup script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories():
    """
    Create the required project directory structure.
    
    Creates:
    - src/
    - tests/
    - data/raw
    - data/processed
    - data/splits
    - results
    - contracts/
    - .github/workflows/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root (current working directory)
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]
    
    success = True
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            # Create the directory and any necessary parent directories
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created/exists: {full_path}")
            
            # Create a .gitkeep file to ensure the directory is tracked by git
            # This is important for empty directories
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                logger.debug(f"Created .gitkeep in: {gitkeep_path}")
                
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
    
    if success:
        logger.info("Project structure setup completed successfully.")
    else:
        logger.error("Project structure setup completed with errors.")
        
    return success

if __name__ == "__main__":
    logger.info("Starting project structure setup...")
    success = setup_directories()
    sys.exit(0 if success else 1)