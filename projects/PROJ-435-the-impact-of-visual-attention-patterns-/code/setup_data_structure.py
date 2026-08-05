import os
import sys
import logging
from pathlib import Path

# Ensure the project root is in the path for imports if running as script
# The project structure assumes this file is in code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    return PROJECT_ROOT

def setup_logging() -> logging.Logger:
    """Configures and returns a logger for the setup process."""
    logger = logging.getLogger("setup_data_structure")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def create_directories(base_path: Path, logger: logging.Logger) -> None:
    """
    Creates the required directory structure for the project.
    
    Required directories:
    - data/raw/
    - data/derived/
    - data/processed/
    - code/ (already exists as parent of this script, but ensures existence)
    - tests/
    - state/
    """
    directories = [
        "data/raw",
        "data/derived",
        "data/processed",
        "tests",
        "state",
        "output" # Added for exclusion logs and other outputs mentioned in tasks
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path.relative_to(base_path)}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path.relative_to(base_path)}")
    
    logger.info(f"Directory setup complete. Created {created_count} new directories.")

def main() -> None:
    """Main entry point for the setup script."""
    logger = setup_logging()
    logger.info("Starting data directory structure setup...")
    
    root = get_project_root()
    logger.info(f"Project root identified at: {root}")
    
    create_directories(root, logger)
    
    logger.info("Setup finished successfully.")

if __name__ == "__main__":
    main()
