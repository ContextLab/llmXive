import os
from pathlib import Path
from typing import List
import logging
from config import get_project_root
from utils.logging import get_logger

def create_directories() -> None:
    """
    Create the project directory structure per the implementation plan.
    
    Directories created:
    - code/data, code/stimuli, code/analysis, code/viz, code/tests
    - data/raw/stimuli, data/raw/responses, data/processed, data/results
    - docs
    """
    root = get_project_root()
    logger = get_logger(__name__)
    
    # Define the directory structure relative to the project root
    directories: List[str] = [
        "code/data",
        "code/stimuli",
        "code/analysis",
        "code/viz",
        "code/tests",
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logger.info(f"Created directory: {full_path}")
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Directory setup complete. Created {created_count} new directories.")

def main() -> None:
    """Entry point for the directory setup script."""
    setup_logger = get_logger(__name__)
    setup_logger.info("Starting project directory setup...")
    create_directories()
    setup_logger.info("Project directory setup finished.")

if __name__ == "__main__":
    main()
