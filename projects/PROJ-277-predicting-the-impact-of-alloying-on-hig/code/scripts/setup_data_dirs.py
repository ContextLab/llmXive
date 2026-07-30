import os
import sys
from pathlib import Path
from config import get_config_from_args
from utils.logger import get_logger

def main():
    """
    Creates the directory tree structure for the project:
    projects/PROJ-277-predicting-oxidation-resistance/
    ├── code/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── tests/
    │   ├── contract/
    │   ├── integration/
    │   └── unit/
    ├── logs/
    └── data/processed/ (for outputs)

    This script is idempotent.
    """
    config = get_config_from_args()
    logger = get_logger(__name__)
    
    # The project root is defined relative to where this script runs or via config
    # Based on task description, we create the structure under the project root.
    # Assuming the script is run from the project root or the config points to it.
    # The task specifies: projects/PROJ-277-predicting-oxidation-resistance/
    # We will create this relative to the current working directory or the config base.
    
    base_path = Path.cwd()
    project_root = base_path / "projects" / "PROJ-277-predicting-oxidation-resistance"
    
    # If the project root doesn't exist, create it
    project_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensuring project root exists: {project_root}")
    
    # Define the subdirectories to create
    # Based on tasks.md and standard conventions
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "logs",
        "figures" # Added for T028/T032c requirements
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Directory setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
