import os
from pathlib import Path
from typing import List
import logging
from ..config import get_project_root
from ..utils.logging import get_logger

logger = get_logger(__name__)

def create_directories():
    """Create all required project directories."""
    root = get_project_root()
    
    directories = [
        root / "code" / "data",
        root / "code" / "stimuli",
        root / "code" / "analysis",
        root / "code" / "viz",
        root / "code" / "utils",
        root / "data" / "raw" / "stimuli",
        root / "data" / "raw" / "responses",
        root / "data" / "processed",
        root / "data" / "results",
        root / "logs",
        root / "figures"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {directory}")
    
    logger.info(f"Created {len(directories)} directories")

def main():
    """Main entry point for project setup."""
    logger.info("Starting project setup")
    create_directories()
    logger.info("Project setup completed")

if __name__ == "__main__":
    main()
