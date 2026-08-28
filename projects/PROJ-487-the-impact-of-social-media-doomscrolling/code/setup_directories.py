import os
import sys
from pathlib import Path
import logging

def create_directories(project_root: Path) -> None:
    """
    Create the required code directory structure for the project.
    
    Creates:
    - code/data/
    - code/tests/
    - code/utils/
    
    Args:
        project_root: The root path of the project (e.g., projects/PROJ-487-...)
    """
    directories = [
        project_root / "code" / "data",
        project_root / "code" / "tests",
        project_root / "code" / "utils",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {directory}")

def main() -> int:
    """
    Main entry point for directory creation.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Determine project root based on task requirements
    # The task specifies the project is at: projects/PROJ-487-the-impact-of-social-media-doomscrolling/
    current_dir = Path(__file__).resolve().parent
    
    # If running from code/, go up one level to project root
    if current_dir.name == "code":
        project_root = current_dir.parent
    else:
        # Assume we are in the project root or a subdirectory
        # Try to find the project root by looking for known markers
        # For now, assume current_dir is the project root if not in code/
        project_root = current_dir
        
        # Check if we need to go up to find the project root
        # If the project root is expected to be 'projects/PROJ-487-...'
        # and we are currently in 'projects/PROJ-487-.../code'
        # The logic above handles the 'code' case.
        # If we are in the project root directly, we create 'code/...'
        
        # Verify if 'code' already exists as a sibling to confirm we are at root
        if not (project_root / "code").exists():
            # We are likely at the project root
            pass
        else:
            # If 'code' exists, we might be inside it or at root
            # The path logic above handles the 'code' subdirectory case
            pass

    try:
        create_directories(project_root)
        logging.info("Successfully created all required code directories.")
        return 0
    except Exception as e:
        logging.error(f"Failed to create directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())