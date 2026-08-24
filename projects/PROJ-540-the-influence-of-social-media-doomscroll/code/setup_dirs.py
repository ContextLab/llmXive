"""
Directory structure setup for the project.
Creates the necessary folders for data, code, outputs, and tests.
"""
import os
import sys
from pathlib import Path
import logging

# Configure basic logging for setup operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure.
    
    Args:
        base_path: The root path where directories should be created.
    """
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {full_path}")
    
    # Create __init__.py files in Python package directories
    python_dirs = [
        "code",
        "tests",
        "projects/PROJ-540-the-influence-of-social-media-doomscroll"
    ]
    
    for dir_path in python_dirs:
        full_path = base_path / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py in: {full_path}")
            created_count += 1
        else:
            logger.info(f"__init__.py already exists in: {full_path}")
    
    logger.info(f"Directory setup complete. Created {created_count} new items.")

def main():
    """Main entry point for directory creation."""
    try:
        # Get the project root (parent of the code directory)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        logger.info(f"Project root identified at: {project_root}")
        create_directories(project_root)
        
        # Verify creation
        required_dirs = [
            "data/raw",
            "data/processed", 
            "code",
            "outputs",
            "tests"
        ]
        
        missing = []
        for dir_path in required_dirs:
            if not (project_root / dir_path).exists():
                missing.append(dir_path)
        
        if missing:
            logger.error(f"Missing required directories: {missing}")
            sys.exit(1)
        else:
            logger.info("All required directories verified successfully.")
            
    except Exception as e:
        logger.error(f"Error during directory creation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
