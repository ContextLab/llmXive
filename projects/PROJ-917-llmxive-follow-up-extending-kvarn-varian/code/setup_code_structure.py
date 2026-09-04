"""
Project setup script to initialize the code/ directory structure.
This script creates the root 'code/' directory and verifies its existence.
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

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    # Try to find the directory containing the project's config or requirements
    current = Path.cwd()
    while current != current.parent:
        if (current / "requirements.txt").exists() or (current / "tasks.md").exists():
            return current
        current = current.parent
    # Fallback to current working directory if no markers found
    return Path.cwd()

def create_directories(project_root: Path) -> bool:
    """
    Create the 'code/' directory if it does not exist.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    code_dir = project_root / "code"
    
    if code_dir.exists():
        logger.info(f"Directory '{code_dir}' already exists.")
        return True
    
    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Successfully created directory: {code_dir}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory '{code_dir}': {e}")
        return False

def verify_structure(project_root: Path) -> bool:
    """
    Verify that the 'code/' directory exists and is a directory.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if the directory exists and is a directory, False otherwise.
    """
    code_dir = project_root / "code"
    if code_dir.exists() and code_dir.is_dir():
        logger.info(f"Verification passed: '{code_dir}' exists and is a directory.")
        return True
    else:
        logger.error(f"Verification failed: '{code_dir}' does not exist or is not a directory.")
        return False

def main():
    """Main entry point for the script."""
    logger.info("Starting code directory structure initialization...")
    
    project_root = get_project_root()
    logger.info(f"Project root identified as: {project_root}")
    
    if not create_directories(project_root):
        logger.error("Directory creation failed. Exiting.")
        sys.exit(1)
    
    if not verify_structure(project_root):
        logger.error("Structure verification failed. Exiting.")
        sys.exit(1)
    
    logger.info("Code directory structure initialization completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
