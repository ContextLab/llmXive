"""
Project initialization script.
Creates the directory structure for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Import logging utility if available, otherwise fallback to basic print
try:
    from utils.logging import setup_logger, get_logger
    LOGGER = setup_logger("setup_project")
except ImportError:
    LOGGER = None

def log(msg: str):
    if LOGGER:
        LOGGER.info(msg)
    else:
        print(msg)

def create_directory_structure(base_path: Path) -> None:
    """
    Creates the standard directory structure for the project.
    
    Args:
        base_path: The root path where directories should be created.
    """
    log(f"Creating directory structure at: {base_path}")
    
    # Define the directory structure
    # code/ subdirectories
    code_dirs = [
        "code/simulation",
        "code/analysis",
        "code/reporting",
        "code/utils",
        "code/data_models"
    ]
    
    # data/ subdirectories
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/interim"
    ]
    
    # tests/ subdirectories
    tests_dirs = [
        "tests/unit",
        "tests/integration"
    ]
    
    # logs/ directory (for logging output)
    logs_dirs = [
        "logs"
    ]
    
    all_dirs = code_dirs + data_dirs + tests_dirs + logs_dirs
    
    created_count = 0
    for dir_name in all_dirs:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            log(f"Created: {full_path}")
            created_count += 1
        else:
            log(f"Exists (skipped): {full_path}")
    
    # Create __init__.py files to make them packages
    for dir_name in code_dirs:
        init_path = base_path / dir_name / "__init__.py"
        if not init_path.exists():
            init_path.touch()
            log(f"Created package init: {init_path}")
        
        # Also create __init__.py for data_models if it's a separate package
        if dir_name == "code/data_models":
            # Already handled above
            pass
    
    for dir_name in tests_dirs:
        init_path = base_path / dir_name / "__init__.py"
        if not init_path.exists():
            init_path.touch()
            log(f"Created package init: {init_path}")
    
    # Create .gitkeep in data directories to ensure they are tracked
    for dir_name in data_dirs:
        keep_path = base_path / dir_name / ".gitkeep"
        if not keep_path.exists():
            keep_path.touch()
            log(f"Created .gitkeep: {keep_path}")
    
    log(f"Directory structure creation complete. Created {created_count} new directories.")

def main():
    """Entry point for the script."""
    # Determine the project root. 
    # Assuming this script runs from projects/PROJ-424-investigating-the-predictive-power-of-mo/
    # We look for the current working directory or the directory containing this file.
    script_dir = Path(__file__).parent
    
    # If the script is in a 'code' subdirectory, the project root is parent of code
    if script_dir.name == "code":
        project_root = script_dir.parent
    else:
        project_root = script_dir
        
    log(f"Project root detected: {project_root}")
    
    try:
        create_directory_structure(project_root)
        log("Setup completed successfully.")
        return 0
    except Exception as e:
        log(f"Error during setup: {e}")
        if LOGGER:
            LOGGER.error("Error during setup", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
