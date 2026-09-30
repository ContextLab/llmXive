import os
import logging
from pathlib import Path

# Configure logging for the setup process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_project_structure(root_dir: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        root_dir: The root directory of the project.
    """
    # Define the required directories relative to the project root
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
        "state",
        "docs",
        "logs",
        "figures",
    ]

    logger.info(f"Creating project structure in: {root_dir}")

    created_count = 0
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Project structure setup complete. Created {created_count} new directories.")

def ensure_init_files(root_dir: Path) -> None:
    """
    Ensure __init__.py files exist in all Python package directories.
    
    Args:
        root_dir: The root directory of the project.
    """
    python_dirs = [
        "code/data",
        "code/preprocess",
        "code/analysis",
        "code/modeling",
        "code/validation",
        "code/report",
        "code/utils",
        "tests",
    ]

    for dir_path_str in python_dirs:
        full_path = root_dir / dir_path_str
        init_file = full_path / "__init__.py"
        
        # Create directory if it doesn't exist (should be handled by create_project_structure)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
        
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py: {init_file}")
        else:
            logger.debug(f"__init__.py already exists: {init_file}")

def main() -> None:
    """
    Main entry point for the setup script.
    Creates the project directory structure and initializes Python packages.
    """
    # Determine project root (parent of the code directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    logger.info(f"Project root detected at: {project_root}")

    try:
        create_project_structure(project_root)
        ensure_init_files(project_root)
        logger.info("Setup completed successfully.")
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
