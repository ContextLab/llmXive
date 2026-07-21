import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(dir_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory to create
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def setup_data_directories(base_path: str) -> bool:
    """
    Set up the standard data directory structure.
    
    Args:
        base_path: Base path for the project
        
    Returns:
        True if all directories were created successfully, False otherwise
    """
    directories = [
        os.path.join(base_path, 'data', 'raw'),
        os.path.join(base_path, 'data', 'processed'),
    ]
    
    success = True
    for dir_path in directories:
        if not ensure_directory(dir_path):
            success = False
    
    return success

def create_project_structure(root_path: str) -> bool:
    """
    Create the full project directory structure for T001a.
    
    Creates:
        - data/raw
        - data/processed
        - code
        - tests
        - results
        
    Args:
        root_path: Root path for the project (projects/PROJ-967-llmxive-follow-up-extending-beyond-scala)
        
    Returns:
        True if all directories were created successfully, False otherwise
    """
    directories = [
        os.path.join(root_path, 'data', 'raw'),
        os.path.join(root_path, 'data', 'processed'),
        os.path.join(root_path, 'code'),
        os.path.join(root_path, 'tests'),
        os.path.join(root_path, 'results'),
    ]
    
    success = True
    for dir_path in directories:
        if not ensure_directory(dir_path):
            success = False
    
    return success

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Set up project directory structure for T001a'
    )
    parser.add_argument(
        '--root-path',
        type=str,
        default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
        help='Root path for the project (default: projects/PROJ-967-llmxive-follow-up-extending-beyond-scala)'
    )
    return parser.parse_args()

def main():
    """Main entry point for the directory setup script."""
    args = parse_args()
    
    logger.info(f"Setting up project directories at: {args.root_path}")
    
    if create_project_structure(args.root_path):
        logger.info("Project directory structure created successfully")
        return 0
    else:
        logger.error("Failed to create some project directories")
        return 1

if __name__ == '__main__':
    sys.exit(main())