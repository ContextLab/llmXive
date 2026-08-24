import os
import sys
import logging
from typing import List

# Configure logging for the setup phase
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> str:
    """
    Returns the absolute path to the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    # If run from code/, go up one level. If run from root, stay.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == 'code':
        return os.path.dirname(current_dir)
    return current_dir

def ensure_dir(path: str) -> None:
    """
    Creates a directory if it does not exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")
    else:
        logger.debug(f"Directory already exists: {path}")

def create_project_structure() -> List[str]:
    """
    Creates the standard project structure as defined in plan.md:
    - code/
    - data/
    - docs/
    - tests/
    
    Returns a list of created/existing directory paths.
    """
    root = get_project_root()
    logger.info(f"Project root identified at: {root}")
    
    directories = [
        'code',
        'data',
        'docs',
        'tests',
        # Subdirectories for data organization
        os.path.join('data', 'raw'),
        os.path.join('data', 'processed'),
        os.path.join('data', 'results'),
        os.path.join('data', 'reports'),
        # Subdirectories for code organization
        os.path.join('code', 'data'),
        os.path.join('code', 'features'),
        os.path.join('code', 'analysis'),
        os.path.join('code', 'utils'),
    ]
    
    created_paths = []
    for dir_path in directories:
        full_path = os.path.join(root, dir_path)
        ensure_dir(full_path)
        created_paths.append(full_path)
    
    return created_paths

def main() -> None:
    """
    Entry point for the setup script.
    Creates the directory structure and prints verification info.
    """
    logger.info("Starting project structure setup...")
    paths = create_project_structure()
    
    logger.info("Project structure setup complete.")
    logger.info(f"Created/Verified {len(paths)} directories:")
    for p in paths:
        logger.info(f"  - {p}")
    
    # Verification step: assert directories exist
    root = get_project_root()
    required_dirs = ['code', 'data', 'docs', 'tests']
    missing = []
    for d in required_dirs:
        if not os.path.isdir(os.path.join(root, d)):
            missing.append(d)
    
    if missing:
        logger.error(f"Verification failed: Missing directories: {missing}")
        sys.exit(1)
    else:
        logger.info("Verification passed: All required directories exist.")

if __name__ == '__main__':
    main()
