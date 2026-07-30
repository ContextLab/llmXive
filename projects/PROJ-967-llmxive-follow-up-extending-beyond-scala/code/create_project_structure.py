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

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The path to ensure exists
        
    Returns:
        True if the directory exists (or was created successfully), False otherwise
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        elif not path.is_dir():
            logger.error(f"Path exists but is not a directory: {path}")
            return False
        return True
    except PermissionError:
        logger.error(f"Permission denied creating directory: {path}")
        return False
    except OSError as e:
        logger.error(f"OS error creating directory {path}: {e}")
        return False

def main():
    """
    Main function to create the project directory structure for PROJ-967.
    Creates the following directories relative to the repository root:
    - data/raw
    - data/processed
    - code
    - tests
    - results
    """
    # Determine the base path (repository root)
    # We assume the script is run from the repository root or the project root
    # The task specifies paths relative to repository root: 
    # projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/...
    
    # Let's define the project root relative to the script location or CWD
    # Assuming the script is in code/ and we need to go up one level to repo root
    # But the task says "relative to repository root", so we construct the full path
    
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    # Define the directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results"
    ]
    
    logger.info(f"Creating project structure under: {project_root}")
    
    success = True
    for directory in directories:
        if not ensure_directory(directory):
            success = False
    
    if success:
        logger.info("Project directory structure created successfully.")
        return 0
    else:
        logger.error("Failed to create some directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())