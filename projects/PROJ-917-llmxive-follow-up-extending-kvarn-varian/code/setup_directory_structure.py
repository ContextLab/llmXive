"""
Project Directory Structure Initialization Script.

This script initializes the core directory structure for the llmXive project,
specifically creating the `code/` directory and its required subdirectories
for data generation, simulation, analysis, and model training as defined
in the project plan.

It serves as the implementation for Task T001a.
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
    Assumes the script is run from the repository root or the 'code' directory.
    Looks for the 'state' directory to anchor the root, otherwise defaults to parent of script.
    """
    current_dir = Path.cwd()
    
    # Check if we are already in the project root (state dir exists)
    if (current_dir / "state").exists():
        return current_dir
    
    # Check if we are in the 'code' directory
    if current_dir.name == "code" and (current_dir.parent / "state").exists():
        return current_dir.parent

    # Fallback: Assume current directory is root if 'requirements.txt' exists
    if (current_dir / "requirements.txt").exists():
        return current_dir
    
    # Last resort: go up one level if 'state' is found there
    if (current_dir.parent / "state").exists():
        return current_dir.parent
        
    logger.warning("Could not definitively locate project root. Using current directory.")
    return current_dir

def create_directories(root_dir: Path) -> bool:
    """
    Create the required directory structure under the code/ directory.
    
    Structure to create:
    code/
    ├── __init__.py
    ├── data_generation/
    │   └── __init__.py
    ├── simulation/
    │   └── __init__.py
    ├── analysis/
    │   └── __init__.py
    ├── model_training/
    │   └── __init__.py
    ├── utils/
    │   └── __init__.py
    ├── entities.py (placeholder to ensure module resolution)
    └── config.py (placeholder to ensure module resolution)
    
    Args:
        root_dir: The project root directory path.
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    code_dir = root_dir / "code"
    
    # Define subdirectories
    subdirs = [
        "data_generation",
        "simulation",
        "analysis",
        "model_training",
        "utils",
        "tests", # Ensure tests is also under code if needed by internal structure
        "tests/test_data_generation",
        "tests/test_model_training",
        "tests/test_simulation",
        "tests/test_analysis",
    ]
    
    success = True
    
    # Ensure code directory itself exists
    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Verified/created directory: {code_dir}")
    except OSError as e:
        logger.error(f"Failed to create code directory: {e}")
        return False
    
    # Create subdirectories
    for subdir_name in subdirs:
        subdir_path = code_dir / subdir_name
        try:
            subdir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Verified/created directory: {subdir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {subdir_path}: {e}")
            success = False
    
    # Create __init__.py files to make them Python packages
    init_paths = [
        code_dir,
        code_dir / "data_generation",
        code_dir / "simulation",
        code_dir / "analysis",
        code_dir / "model_training",
        code_dir / "utils",
        code_dir / "tests",
        code_dir / "tests" / "test_data_generation",
        code_dir / "tests" / "test_model_training",
        code_dir / "tests" / "test_simulation",
        code_dir / "tests" / "test_analysis",
    ]
    
    for init_path in init_paths:
        init_file = init_path / "__init__.py"
        try:
            # Only create if it doesn't exist to avoid overwriting user edits
            if not init_file.exists():
                init_file.touch()
                logger.info(f"Created __init__.py: {init_file}")
            else:
                logger.debug(f"__init__.py already exists: {init_file}")
        except OSError as e:
            logger.error(f"Failed to create __init__.py at {init_file}: {e}")
            success = False
    
    return success

def verify_structure(root_dir: Path) -> bool:
    """
    Verify that the required directory structure exists.
    
    Args:
        root_dir: The project root directory path.
        
    Returns:
        True if all required directories exist, False otherwise.
    """
    code_dir = root_dir / "code"
    required_dirs = [
        "data_generation",
        "simulation",
        "analysis",
        "model_training",
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = code_dir / dir_name
        if not dir_path.exists():
            logger.error(f"Missing required directory: {dir_path}")
            all_exist = False
        elif not dir_path.is_dir():
            logger.error(f"Path exists but is not a directory: {dir_path}")
            all_exist = False
        
        # Check for __init__.py
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            logger.warning(f"Missing __init__.py in: {dir_path}")
            # Not strictly fatal for directory existence, but good to note
    
    if code_dir.exists():
        logger.info(f"Verification passed: {code_dir} exists.")
    else:
        logger.error(f"Verification failed: {code_dir} does not exist.")
        all_exist = False
        
    return all_exist

def main():
    """
    Main entry point for the directory structure initialization.
    """
    logger.info("Starting directory structure initialization for T001a...")
    
    root_dir = get_project_root()
    logger.info(f"Detected project root: {root_dir}")
    
    if not create_directories(root_dir):
        logger.error("Failed to create directory structure.")
        sys.exit(1)
        
    if not verify_structure(root_dir):
        logger.error("Verification failed after creation.")
        sys.exit(1)
        
    logger.info("Directory structure initialization completed successfully.")
    logger.info(f"Verified 'code/' directory and subdirectories exist at: {root_dir / 'code'}")

if __name__ == "__main__":
    main()