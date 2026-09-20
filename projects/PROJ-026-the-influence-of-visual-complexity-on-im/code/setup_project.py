"""
Project initialization script.

Creates the initial project structure and configuration files.
"""
import os
from pathlib import Path
from typing import List
import logging
from config import get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directories() -> None:
    """
    Create the full project directory structure.
    
    This function creates all necessary directories for the research pipeline.
    """
    project_root = get_project_root()
    
    directories: List[str] = [
        # Code modules
        "code/data",
        "code/stimuli",
        "code/analysis",
        "code/viz",
        "code/tests",
        "code/utils",
        
        # Data directories
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        
        # Documentation
        "docs",
        
        # Logs
        "logs"
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        else:
            logger.debug(f"Directory already exists: {full_path}")

def main() -> None:
    """Entry point for project setup."""
    create_directories()
    print("Project structure initialized successfully.")

if __name__ == "__main__":
    main()