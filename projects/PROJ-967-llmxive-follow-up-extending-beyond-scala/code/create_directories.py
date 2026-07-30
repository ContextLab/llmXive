import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to create the required project directory structure.
    
    Creates the following directories relative to the repository root:
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results
    """
    # Determine repository root (assuming script is in code/ directory)
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    
    project_root = repo_root / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"
    
    # Define required directories
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results"
    ]
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Creating {len(required_dirs)} directories...")
    
    success_count = 0
    for dir_path in required_dirs:
        if ensure_directory(dir_path):
            success_count += 1
    
    logger.info(f"Successfully created {success_count}/{len(required_dirs)} directories")
    
    if success_count == len(required_dirs):
        logger.info("All required directories created successfully")
        return 0
    else:
        logger.error("Some directories failed to create")
        return 1

if __name__ == "__main__":
    sys.exit(main())