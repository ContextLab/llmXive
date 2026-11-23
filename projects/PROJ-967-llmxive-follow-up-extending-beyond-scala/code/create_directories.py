import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object representing the directory to create
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Create the project directory structure for PROJ-967-llmxive-follow-up-extending-beyond-scala.
    
    Creates the following directories relative to the repository root:
    - data/raw
    - data/processed
    - results
    - code
    - tests
    """
    # Determine project root relative to this script's location
    # Assuming this script is in code/ directory
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"
    
    # Define directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests",
    ]
    
    logger.info(f"Creating project structure at: {project_root}")
    
    success = True
    for directory in directories:
        if not ensure_directory(directory):
            success = False
    
    if success:
        logger.info("Project directory structure created successfully.")
        # Print created structure for verification
        logger.info("Created directories:")
        for directory in directories:
            logger.info(f"  - {directory.relative_to(project_root.parent)}")
    else:
        logger.error("Some directories failed to create.")
        sys.exit(1)

if __name__ == "__main__":
    main()