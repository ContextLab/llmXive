"""
Script to create the project directory structure for PROJ-967.
This implements Task T001a by ensuring all required directories exist.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists. Create it if it doesn't.
    
    Args:
        path: The directory path to ensure exists
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main function to create the project directory structure.
    """
    # Define the project root relative to the script location or current working directory
    # Assuming this script is run from the repository root
    repo_root = Path.cwd()
    project_root = repo_root / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"
    
    # Define required directories as per T001a
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests"
    ]
    
    # Also ensure package directories exist
    package_dirs = [
        project_root / "code",
        project_root / "tests"
    ]
    
    logger.info(f"Creating project structure in: {project_root}")
    
    success = True
    for dir_path in required_dirs:
        if not ensure_directory(dir_path):
            success = False
    
    # Create __init__.py files to make code and tests proper Python packages
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "tests" / "__init__.py"
    ]
    
    for init_file in init_files:
        try:
            if not init_file.exists():
                init_file.write_text("# Package initialization\n")
                logger.info(f"Created package init: {init_file}")
            else:
                logger.info(f"Package init already exists: {init_file}")
        except Exception as e:
            logger.error(f"Failed to create {init_file}: {e}")
            success = False
    
    # Create .gitkeep files in data directories to ensure they are tracked
    gitkeep_files = [
        project_root / "data" / "raw" / ".gitkeep",
        project_root / "data" / "processed" / ".gitkeep",
        project_root / "results" / ".gitkeep"
    ]
    
    for gitkeep in gitkeep_files:
        try:
            if not gitkeep.exists():
                gitkeep.write_text("# Placeholder to ensure directory is tracked\n")
                logger.info(f"Created .gitkeep: {gitkeep}")
            else:
                logger.info(f".gitkeep already exists: {gitkeep}")
        except Exception as e:
            logger.error(f"Failed to create {gitkeep}: {e}")
            success = False
    
    if success:
        logger.info("Project directory structure created successfully.")
        return 0
    else:
        logger.error("Some directories or files could not be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
