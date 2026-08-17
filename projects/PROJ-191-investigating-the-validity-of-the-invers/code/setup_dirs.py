"""
Project Directory Setup Script for PROJ-191.

This script creates the full project directory tree required for the
'Investigating the Validity of the Inverse-Square Law at Sub-Millimeter Scales'
project. It ensures all necessary sub-directories exist under the project root.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Creates the full project directory tree at the repository root.
    
    Target root: projects/PROJ-191-investigating-the-validity-of-the-invers/
    Sub-directories include code/, tests/, data/, docs/, and specific
    sub-structures for data processing, models, inference, etc.
    """
    # Define the project root relative to the script location or repository root
    # Assuming the script runs from the repository root or code/
    repo_root = Path.cwd()
    
    # The specific project directory as defined in the task
    project_name = "PROJ-191-investigating-the-validity-of-the-invers"
    project_root = repo_root / "projects" / project_name
    
    # Define the required directory structure
    # Base directories
    base_dirs = [
        "code",
        "tests",
        "data",
        "docs"
    ]
    
    # Specific sub-directories for code
    code_subdirs = [
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils"
    ]
    
    # Specific sub-directories for data
    data_subdirs = [
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    # Specific sub-directories for tests
    tests_subdirs = [
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    # Combine all directories to create
    all_dirs = base_dirs + code_subdirs + data_subdirs + tests_subdirs
    
    logger.info(f"Ensuring project directory structure at: {project_root}")
    
    created_count = 0
    existing_count = 0
    
    for dir_name in all_dirs:
        full_path = project_root / dir_name
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                sys.exit(1)
        else:
            existing_count += 1
    
    logger.info(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    logger.info(f"Project root initialized at: {project_root}")
    
    # Verify the structure exists
    if not project_root.exists():
        logger.error("Project root was not created successfully.")
        sys.exit(1)
        
    return 0

if __name__ == "__main__":
    sys.exit(main())