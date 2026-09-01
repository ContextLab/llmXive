"""
Project Structure Setup Module.

This module provides utilities to create and verify the project directory structure
as defined in plan.md. It ensures that the required directories exist and are ready
for data, code, documentation, and testing artifacts.
"""
import os
import sys
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> str:
    """
    Get the absolute path to the project root directory.
    
    The project root is assumed to be the directory containing this module's parent 'code' folder.
    Returns the absolute path to the project root.
    """
    current_file_path = os.path.abspath(__file__)
    code_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(code_dir)
    return project_root

def ensure_dir(dir_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Absolute or relative path to the directory.
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    else:
        logger.debug(f"Directory already exists: {dir_path}")

def create_project_structure() -> List[str]:
    """
    Create the standard project directory structure.
    
    Creates the following directories under the project root:
    - code/
    - data/
    - docs/
    - tests/
    
    Returns:
        List of created directory paths.
    """
    project_root = get_project_root()
    required_dirs = [
        'code',
        'data',
        'docs',
        'tests'
    ]
    
    created_dirs = []
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        ensure_dir(dir_path)
        created_dirs.append(dir_path)
        
    logger.info(f"Project structure verified/created at: {project_root}")
    return created_dirs

def verify_structure() -> bool:
    """
    Verify that the required project directories exist.
    
    Returns:
        True if all required directories exist, False otherwise.
    """
    project_root = get_project_root()
    required_dirs = ['code', 'data', 'docs', 'tests']
    
    missing = []
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if not os.path.isdir(dir_path):
            missing.append(dir_name)
    
    if missing:
        logger.error(f"Missing required directories: {missing}")
        return False
    
    logger.info("All required project directories exist.")
    return True

def main() -> None:
    """
    Main entry point for project structure setup.
    
    Creates the required directories and verifies the structure.
    Prints a tree-like listing of the created structure to stdout for verification.
    """
    logger.info("Starting project structure setup...")
    
    # Create directories
    create_project_structure()
    
    # Verify
    if not verify_structure():
        logger.error("Project structure verification failed.")
        sys.exit(1)
    
    # Print tree-like output for verification
    project_root = get_project_root()
    print(f"\nProject Structure at: {project_root}\n")
    print("code/")
    print("data/")
    print("docs/")
    print("tests/")
    print("\nVerification successful: All required directories exist.\n")

if __name__ == '__main__':
    main()
