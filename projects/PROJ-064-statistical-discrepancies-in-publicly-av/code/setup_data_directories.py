"""
Module to set up the required data directory structure for the project.

This script ensures that the following directories exist under the project root:
- data/raw/
- data/processed/
- state/

It also creates a .gitkeep file in each directory to ensure they are tracked by Git.
"""
import os
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_data_directories(project_root: str) -> None:
    """
    Create the required data directory structure.
    
    Args:
        project_root: Path to the project root directory
        
    Raises:
        ValueError: If project_root is not a valid directory
    """
    project_path = Path(project_root)
    
    if not project_path.exists():
        raise ValueError(f"Project root directory does not exist: {project_root}")
    
    if not project_path.is_dir():
        raise ValueError(f"Project root is not a directory: {project_root}")
    
    # Define required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "state"
    ]
    
    created_dirs = []
    skipped_dirs = []
    
    for dir_path in required_dirs:
        full_path = project_path / dir_path
        
        try:
            # Create directory if it doesn't exist
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep file to ensure directory is tracked by Git
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
            
            created_dirs.append(str(full_path))
            logger.info(f"Created directory: {full_path}")
            
        except PermissionError:
            logger.error(f"Permission denied when creating directory: {full_path}")
            raise
        except Exception as e:
            logger.error(f"Error creating directory {full_path}: {e}")
            raise
    
    # Log summary
    logger.info(f"Successfully created {len(created_dirs)} directories")
    for dir_path in created_dirs:
        logger.info(f"  - {dir_path}")
    
    # Verify all required directories exist
    for dir_path in required_dirs:
        full_path = project_path / dir_path
        if not full_path.exists() or not full_path.is_dir():
            raise RuntimeError(f"Failed to create required directory: {full_path}")
    
    logger.info("All required data directories are set up and verified")

def main():
    """
    Main entry point for the script.
    
    Usage:
        python setup_data_directories.py [project_root]
        
    If project_root is not provided, defaults to the current working directory.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Set up the required data directory structure for the project."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=os.getcwd(),
        help="Path to the project root directory (default: current working directory)"
    )
    
    args = parser.parse_args()
    
    try:
        setup_data_directories(args.project_root)
        print(f"Data directory structure successfully set up in: {args.project_root}")
        sys.exit(0)
    except Exception as e:
        print(f"Error setting up data directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
