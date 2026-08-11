import os
import sys
import logging
from pathlib import Path
from utils.logging_config import get_logger

def setup_directories(project_root: Path) -> None:
    """
    Creates the required directory structure for the PROJ-328 project.
    This function ensures all necessary folders exist before any data processing
    or model training begins.
    """
    logger = get_logger(__name__)
    
    # Define the specific directories required by T001
    # Note: The task specifies `projects/PROJ-328-predicting-the-impact-of-composition-on-/` as the root context,
    # but the execution environment is `code/`. We create the structure relative to the project root.
    # The task lists: `data/raw`, `data/processed`, `data/outputs`, `code/`, `code/ingestion`, 
    # `code/features`, `code/models`, `code/evaluation`, `code/visualization`, `tests/`, `models/`.
    
    directories = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "tests",
        "models"
    ]
    
    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
            skipped_count += 1

    logger.info(f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}")

def main():
    """
    Entry point for the project structure setup script.
    """
    # Determine project root (assuming script is run from the root or 'code' directory)
    # We look for the root by checking if 'data' and 'code' exist relative to the script location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if (script_dir / "data").exists() else script_dir

    # If we are in 'code/', project_root is the parent. If we are at root, it's here.
    # The task implies we are setting up the structure from the project root.
    
    logger = get_logger(__name__)
    logger.info(f"Starting project structure setup from: {project_root}")
    
    try:
        setup_directories(project_root)
        logger.info("Project structure setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to setup project structure: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
