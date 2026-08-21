import os
import sys
import logging
from pathlib import Path

# Import from existing API surface
from config import ensure_directories

def main():
    """
    Create the required project directory structure for llmXive follow-up.
    
    Creates:
    - code/, tests/, docs/, specs/
    - data/raw/, data/processed/, data/validation/, data/models/, data/results/, data/logs/
    
    Returns exit code 0 on success, 1 on failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Define all required directories relative to project root
    # We assume the script is run from the project root
    project_root = Path.cwd()
    
    # Top-level directories
    top_level_dirs = [
        'code',
        'tests',
        'docs',
        'specs'
    ]
    
    # Data subdirectories
    data_subdirs = [
        'data/raw',
        'data/processed',
        'data/validation',
        'data/models',
        'data/results',
        'data/logs'
    ]
    
    all_dirs = top_level_dirs + data_subdirs
    
    logger.info(f"Creating project directory structure at: {project_root}")
    
    created_count = 0
    for dir_path in all_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if not full_path.exists():
                raise RuntimeError(f"Failed to create directory: {full_path}")
            created_count += 1
            logger.debug(f"Created directory: {full_path}")
        except Exception as e:
            logger.error(f"Error creating directory {full_path}: {e}")
            sys.exit(1)
    
    logger.info(f"Successfully created {created_count} directories.")
    
    # Verification: run ls -d check equivalent
    verification_dirs = ['code', 'tests', 'data', 'docs', 'specs']
    for dir_name in verification_dirs:
        check_path = project_root / dir_name
        if not check_path.exists() or not check_path.is_dir():
            logger.error(f"Verification failed: {dir_name} does not exist or is not a directory")
            sys.exit(1)
    
    logger.info("Verification passed: All required top-level directories exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
