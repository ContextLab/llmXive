"""
Script to create the project directory structure as defined in the implementation plan.
"""
import os
import logging
from pathlib import Path
from config import get_project_root

# Configure logging for setup operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_directories() -> None:
    """
    Creates the required directory tree for the project.
    
    Creates:
    - code/{data,stimuli,analysis,viz,tests}
    - data/{raw/stimuli,raw/responses,processed,results}
    - docs
    """
    project_root = get_project_root()
    logger.info(f"Project root detected at: {project_root}")
    
    # Define directory structure relative to project root
    # Note: 'tests' is created under project root as per standard convention,
    # though task description mentions 'code/tests'. We will create both to be safe
    # or follow the specific instruction: "code/{data,stimuli,analysis,viz,tests}"
    
    # Based on task T001 description:
    # mkdir -p code/{data,stimuli,analysis,viz,tests} 
    # data/{raw/stimuli,raw/responses,processed,results} docs
    
    dirs_to_create = [
        # Code sub-packages
        "code/data",
        "code/stimuli",
        "code/analysis",
        "code/viz",
        "code/tests", # Explicitly requested in T001 description
        
        # Data sub-structures
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results",
        
        # Documentation
        "docs"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = Path(project_root) / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    logger.info(f"Successfully created {created_count} directories.")


def main() -> None:
    """Entry point for directory setup."""
    try:
        setup_directories()
        logger.info("Project structure initialization complete.")
    except Exception as e:
        logger.error(f"Project structure initialization failed: {e}")
        raise


if __name__ == "__main__":
    main()
