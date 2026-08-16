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

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object representing the directory to create
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
    except PermissionError:
        logger.error(f"Permission denied when creating directory: {path}")
        raise
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise

def setup_data_directories(base_path: Path) -> None:
    """
    Setup data directory structure for the project.
    
    Args:
        base_path: Base path for the project
    """
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed"
    ]
    for dir_path in data_dirs:
        ensure_directory(dir_path)

def create_project_structure(base_path: Path) -> None:
    """
    Create the main project structure directories.
    
    Args:
        base_path: Base path for the project
    """
    project_dirs = [
        base_path / "code",
        base_path / "tests",
        base_path / "results"
    ]
    for dir_path in project_dirs:
        ensure_directory(dir_path)

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Setup project directory structure for llmXive follow-up"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Path to the project root directory"
    )
    return parser.parse_args()

def main() -> int:
    """
    Main function to setup project directories.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    args = parse_args()
    project_root = Path(args.project_root)
    
    logger.info(f"Setting up project directories at: {project_root}")
    
    try:
        # Ensure project root exists
        ensure_directory(project_root)
        
        # Setup data directories
        setup_data_directories(project_root)
        
        # Create main project structure
        create_project_structure(project_root)
        
        logger.info("Project directory structure setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to setup project directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
