"""
Script to create project directory structure.
"""
import os
import sys
import logging
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import ensure_directories, DATA_ROOT, RESULTS_ROOT

def main():
    logger = setup_logging()
    logger.info("Creating project directory structure...")
    
    # Define directories to create
    directories = [
        DATA_ROOT,
        f"{DATA_ROOT}/raw",
        f"{DATA_ROOT}/processed",
        "code",
        f"{RESULTS_ROOT}/models",
        f"{RESULTS_ROOT}/figures",
        "tests",
        "contracts",
        "research",
        "logs",
    ]
    
    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
    
    # Create .gitkeep files
    gitkeep_paths = [
        Path(DATA_ROOT) / ".gitkeep",
        Path(DATA_ROOT) / "raw" / ".gitkeep",
    ]
    
    for keep_path in gitkeep_paths:
        if not keep_path.exists():
            keep_path.touch()
            logger.info(f"Created .gitkeep: {keep_path}")
    
    logger.info("Project directory structure setup complete.")

if __name__ == "__main__":
    main()
