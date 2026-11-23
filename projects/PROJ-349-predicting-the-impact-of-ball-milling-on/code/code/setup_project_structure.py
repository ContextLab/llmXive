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

def setup_directories(base_path: Path) -> None:
    """
    Creates the required project directory structure.
    
    Args:
        base_path: The root directory where the structure will be created.
    """
    # Define the required directories relative to the base path
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]

    created_count = 0
    existing_count = 0

    for dir_name in directories:
        full_path = base_path / dir_name
        
        if full_path.exists():
            logger.info(f"Directory already exists: {full_path}")
            existing_count += 1
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                raise

    logger.info(f"Setup complete. Created {created_count} directories, skipped {existing_count} existing.")

def main():
    """
    Entry point for the setup script.
    Creates the directory structure relative to the script's location or current working directory.
    """
    # Determine base path: prefer script location if run directly, else cwd
    if __name__ == "__main__":
        # If run as `python code/setup_project_structure.py`, base is code/
        # If run as `python setup_project_structure.py` from root, base is .
        script_path = Path(__file__).resolve()
        # Check if we are in the 'code' subdirectory structure or root
        if script_path.parent.name == 'code' and (script_path.parent.parent / 'code').exists():
            base = script_path.parent.parent
        else:
            base = Path.cwd()
    else:
        base = Path.cwd()

    logger.info(f"Setting up project structure in: {base}")
    setup_directories(base)
    logger.info("Project structure verification successful.")

if __name__ == "__main__":
    main()
