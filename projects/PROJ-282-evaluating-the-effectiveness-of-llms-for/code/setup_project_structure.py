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

def create_structure(root_dir: Path) -> None:
    """
    Create the required project directory structure.
    
    Args:
        root_dir: The root directory of the project
    """
    # Define the required directories relative to root
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "state",
        "code",
        "code/src",
        "code/src/utils",
        "code/src/data",
        "code/src/models",
        "code/src/analysis",
        "code/tests",
        "code/tests/unit",
        "code/data",
        "code/specs",
        "code/specs/001-evaluating-the-effectiveness-of-llms-for",
        "code/contracts",
        "code/figures"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = root_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            # Create __init__.py in Python package directories
            if "src" in dir_path or "tests" in dir_path or "code" in dir_path:
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
    
    logger.info(f"Project structure setup complete. Created {created_count} directories, {existing_count} already existed.")

def main():
    """Main entry point for the project structure setup."""
    # Determine the root directory (parent of this script's location)
    current_file = Path(__file__).resolve()
    root_dir = current_file.parent.parent  # Go up two levels to project root
    
    logger.info(f"Setting up project structure at: {root_dir}")
    create_structure(root_dir)
    logger.info("Task T001 completed successfully.")

if __name__ == "__main__":
    main()