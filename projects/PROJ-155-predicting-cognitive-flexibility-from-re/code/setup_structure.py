"""
Project Structure Setup Module.

This module ensures the creation of the required directory structure
for the llmXive research pipeline as defined in plan.md.
"""
import os
import sys
import logging
from typing import List

# Configure logging for the setup process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_dir(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Absolute or relative path to the directory.

    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.info(f"Created directory: {directory_path}")
        else:
            logger.debug(f"Directory already exists: {directory_path}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied creating directory {directory_path}: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error creating directory {directory_path}: {e}")
        return False


def get_project_root() -> str:
    """
    Determine the project root directory.

    Assumes the script is run from the project root or a subdirectory.
    Looks for the 'code' directory to anchor the root if running from within 'code'.

    Returns:
        Absolute path to the project root.
    """
    current_dir = os.getcwd()
    
    # If we are inside 'code', go up one level
    if os.path.basename(current_dir) == 'code':
        return os.path.dirname(current_dir)
    
    # Check if 'code' exists in current dir
    if os.path.exists(os.path.join(current_dir, 'code')):
        return current_dir
    
    # Fallback: assume current dir is root
    logger.warning("Could not locate 'code' directory. Assuming current directory is root.")
    return current_dir


def create_project_structure(root_path: str) -> bool:
    """
    Create the standard project directory structure.

    Creates:
        - code/
        - data/
        - docs/
        - tests/

    Args:
        root_path: The base path where the structure should be created.

    Returns:
        True if all directories were created/verified successfully.
    """
    required_dirs = ['code', 'data', 'docs', 'tests']
    success = True

    for dir_name in required_dirs:
        full_path = os.path.join(root_path, dir_name)
        if not ensure_dir(full_path):
            success = False
            logger.error(f"Failed to create required directory: {dir_name}")
    
    # Create subdirectories for better organization
    subdirs = [
        os.path.join('data', 'raw'),
        os.path.join('data', 'processed'),
        os.path.join('data', 'results'),
        os.path.join('code', 'data'),
        os.path.join('code', 'utils'),
        os.path.join('code', 'features'),
        os.path.join('code', 'analysis'),
        os.path.join('docs', 'specs')
    ]

    for subdir in subdirs:
        full_path = os.path.join(root_path, subdir)
        if not ensure_dir(full_path):
            success = False
            logger.warning(f"Failed to create optional subdirectory: {subdir}")

    return success


def main() -> int:
    """
    Main entry point for the setup script.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Starting project structure setup...")
    
    root = get_project_root()
    logger.info(f"Project root detected at: {root}")

    if create_project_structure(root):
        logger.info("Project structure setup completed successfully.")
        # Verification step
        print("\nVerification: Running tree command logic...")
        required = ['code', 'data', 'docs', 'tests']
        all_exist = True
        for d in required:
            path = os.path.join(root, d)
            exists = os.path.isdir(path)
            status = "✓" if exists else "✗"
            print(f"  {status} {d}/ : {exists}")
            if not exists:
                all_exist = False
        
        if all_exist:
            print("\nAll required directories verified.")
            return 0
        else:
            print("\nVerification FAILED: Some directories missing.")
            return 1
    else:
        logger.error("Project structure setup failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
