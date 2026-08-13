import os
import sys
import logging
from pathlib import Path
from utils.logging_config import get_logger

def setup_directories(base_path: Path) -> None:
    """
    Create the project directory structure as defined in T001.
    
    Creates the following directories relative to base_path:
    - data/raw
    - data/processed
    - data/outputs
    - code/ingestion
    - code/features
    - code/models
    - code/evaluation
    - code/visualization
    - tests/
    - models/
    
    Also ensures the root 'code' directory exists if not already present.
    """
    logger = get_logger(__name__)
    
    # Define the relative paths to create
    relative_paths = [
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
    for rel_path in relative_paths:
        full_path = base_path / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    # Ensure the main 'code' directory exists (it might be created by the sub-paths above, 
    # but we explicitly check/ensure it)
    code_root = base_path / "code"
    if not code_root.exists():
        code_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {code_root}")
        created_count += 1
        
    logger.info(f"Directory setup complete. Created {created_count} new directories.")

def main():
    """
    Main entry point for the setup script.
    Expects to be run from the project root or accepts a path argument.
    """
    # Determine base path: use current working directory
    base_path = Path.cwd()
    
    # Check if we are inside the specific project folder or if we need to navigate
    # The task specifies: projects/PROJ-328-predicting-the-impact-of-composition-on-/
    # If the script is run from the repo root, we might need to target that specific subfolder.
    # However, standard practice for these scripts is to run from the project root.
    # We will assume the script is run from the root of the project tree where these dirs should exist.
    
    print(f"Setting up directory structure in: {base_path}")
    setup_directories(base_path)
    print("Done.")

if __name__ == "__main__":
    main()
