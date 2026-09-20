import os
import logging
from pathlib import Path
from config import get_project_root

logger = logging.getLogger(__name__)

def setup_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    
    Directories to create:
    - code/{data,stimuli,analysis,viz,tests}
    - data/{raw/stimuli,raw/responses,processed,results}
    - docs
    """
    root = get_project_root()
    
    directories = [
        # Code structure
        root / "code" / "data",
        root / "code" / "stimuli",
        root / "code" / "analysis",
        root / "code" / "viz",
        root / "code" / "tests",
        
        # Data structure
        root / "data" / "raw" / "stimuli",
        root / "data" / "raw" / "responses",
        root / "data" / "processed",
        root / "data" / "results",
        
        # Documentation
        root / "docs",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {directory}")
    
    logger.info(f"Setup complete. Created {created_count} new directories.")
    return created_count

def main():
    """Entry point for directory setup script."""
    setup_directories()
