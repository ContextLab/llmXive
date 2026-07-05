import os
from pathlib import Path
import logging
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_state_project_directories(project_ids: List[str]) -> None:
    """
    Create the directory structure for specified project IDs under state/projects/.
    
    Args:
        project_ids: List of project identifiers (e.g., 'PROJ-345')
    """
    base_path = Path("state/projects")
    
    for project_id in project_ids:
        project_dir = base_path / project_id
        
        # Create the main project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created project directory: {project_dir}")
        
        # Create subdirectories for project state artifacts
        subdirs = [
            "logs",
            "snapshots",
            "artifacts",
            "reports"
        ]
        
        for subdir in subdirs:
            subdir_path = project_dir / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  Created subdirectory: {subdir_path}")
        
        # Create a .gitkeep file in each directory to ensure they are tracked
        # even if empty
        keep_file = project_dir / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
            logger.info(f"  Created .gitkeep in {project_dir}")

def main() -> None:
    """
    Main entry point for setting up state project directories.
    Specifically handles PROJ-345 as per the current task.
    """
    logger.info("Starting state project directory setup...")
    
    # Define the specific project ID for this task
    project_ids = ["PROJ-345"]
    
    try:
        create_state_project_directories(project_ids)
        logger.info("State project directory setup completed successfully.")
    except Exception as e:
        logger.error(f"Failed to create state project directories: {e}")
        raise

if __name__ == "__main__":
    main()
