import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def create_project_structure(root: Path) -> None:
    """
    Create the required directory structure for the project.
    
    This function ensures the following directories exist relative to the root:
    - data/raw/
    - data/processed/
    - code/data/
    - code/preprocess/
    - code/analysis/
    - code/modeling/
    - code/validation/
    - code/report/
    - tests/
    
    Args:
        root: The project root directory path.
    """
    # Define the required directory paths relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "tests",
    ]

    for dir_name in required_dirs:
        dir_path = root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

def ensure_init_files(root: Path) -> None:
    """
    Create __init__.py files in all code and tests subdirectories to make them Python packages.
    
    Args:
        root: The project root directory path.
    """
    # Define the directories that need __init__.py files
    package_dirs = [
        "code",
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "tests",
    ]

    for dir_name in package_dirs:
        dir_path = root / dir_name
        init_file = dir_path / "__init__.py"
        
        # Create the directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if it doesn't exist
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py: {init_file}")
        else:
            logger.debug(f"__init__.py already exists: {init_file}")

def main() -> None:
    """
    Main entry point for setting up the project structure.
    
    This function sets up logging, determines the project root,
    creates the directory structure, and ensures __init__.py files exist.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine the project root (assumes this script is in code/setup_structure.py)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    logger.info(f"Project root: {project_root}")
    
    # Create directory structure
    create_project_structure(project_root)
    
    # Ensure __init__.py files exist
    ensure_init_files(project_root)
    
    logger.info("Project structure setup complete.")

if __name__ == "__main__":
    main()
