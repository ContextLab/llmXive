"""
Task T005a: Create data directory structure.

This script creates the required data directories for the project:
- data/raw
- data/curated
- data/eval
- data/validation

It uses the project root defined in the task context and ensures
all directories exist before completion.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Create the data directory structure."""
    # Determine project root based on task context
    # The task specifies the project is at:
    # projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    # We need to create directories relative to the project root (which is 'code' here)
    
    # Get the current working directory or project root
    # Since this script is in code/, we assume we run from code/ or project root
    current_dir = Path.cwd()
    
    # Check if we are in the code directory or project root
    if current_dir.name == 'code':
        project_root = current_dir
    else:
        # Assume we are in the project root (one level up from code/)
        project_root = current_dir / 'code'
    
    # Ensure the project root exists
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    # Define the data directories to create
    data_dirs = [
        'data/raw',
        'data/curated',
        'data/eval',
        'data/validation'
    ]
    
    created_dirs = []
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        
        # Create the directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_dirs.append(full_path)
        else:
            logger.info(f"Directory already exists: {full_path}")
    
    # Verify all directories were created
    missing_dirs = [d for d in data_dirs if not (project_root / d).exists()]
    if missing_dirs:
        logger.error(f"Failed to create directories: {missing_dirs}")
        sys.exit(1)
    
    logger.info(f"Successfully created {len(created_dirs)} data directories.")
    logger.info(f"Data directory structure is ready for T005a.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())