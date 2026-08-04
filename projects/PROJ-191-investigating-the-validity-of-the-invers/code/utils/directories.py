"""
Directory structure management for the llmXive science pipeline.

This module provides robust utilities to ensure the project's required
directory structure exists, implementing 'mkdir -p' logic with proper
error handling and logging.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List

# Import project configuration for logging setup
from config import get_logger, setup_logging

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "code/models",
    "code/inference",
    "code/robustness",
    "code/utils",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "docs",
    "figures",
]

def ensure_data_directories(project_root: Path) -> List[Path]:
    """
    Ensures all required directories exist under the project root.
    
    This function implements robust 'mkdir -p' logic:
    - Creates parent directories if they don't exist
    - Does not raise an error if the directory already exists
    - Validates that the path is actually a directory after creation
    - Logs success/failure for each directory
    
    Args:
        project_root: The root path of the project (e.g., projects/PROJ-191-...)
        
    Returns:
        A list of Path objects for all successfully created/verified directories.
        
    Raises:
        RuntimeError: If any required directory cannot be created or verified.
    """
    logger = get_logger(__name__)
    created_dirs: List[Path] = []
    errors: List[str] = []

    for dir_rel_path in REQUIRED_DIRS:
        target_path = project_root / dir_rel_path
        
        try:
            # Create the directory and all parent directories (mkdir -p behavior)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Verify the path is actually a directory
            if not target_path.is_dir():
                error_msg = f"Failed to verify directory: {target_path} is not a directory"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
            
            created_dirs.append(target_path)
            logger.debug(f"Verified directory: {target_path}")
            
        except PermissionError:
            error_msg = f"Permission denied creating directory: {target_path}"
            errors.append(error_msg)
            logger.error(error_msg)
        except OSError as e:
            error_msg = f"OS error creating directory {target_path}: {e}"
            errors.append(error_msg)
            logger.error(error_msg)

    if errors:
        raise RuntimeError(f"Failed to create {len(errors)} required directories:\n" + "\n".join(errors))

    logger.info(f"Successfully ensured {len(created_dirs)} directories exist.")
    return created_dirs

def main() -> int:
    """
    Main entry point for CLI execution.
    
    Parses command-line arguments to determine the project root,
    then ensures all required directories exist.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)

    # Determine project root
    # Default to current working directory if no argument provided
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path.cwd()
    
    logger.info(f"Ensuring directories for project root: {project_root}")

    try:
        ensure_data_directories(project_root)
        logger.info("Directory structure setup complete.")
        return 0
    except RuntimeError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during directory setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())