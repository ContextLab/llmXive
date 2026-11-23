"""
Project structure initialization script for llmXive pipeline.
Creates required directory hierarchy for the research project.
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

def create_directories(base_path: Path, directories: list) -> None:
    """
    Create a list of directories under the base path.
    
    Args:
        base_path: The root directory for the project
        directories: List of relative directory paths to create
    """
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

def main() -> None:
    """
    Main entry point for project structure setup.
    Creates all required directories for the research pipeline.
    """
    # Determine project root based on task context
    # The task specifies: projects/PROJ-096-exploring-the-role-of-network-topology-o/
    project_root = Path(__file__).parent.parent / "projects" / "PROJ-096-exploring-the-role-of-network-topology-o"
    
    # Ensure project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Project root: {project_root}")
    
    # Define all required directories relative to project root
    required_dirs = [
        "code/utils",
        "code/data",
        "data/raw",
        "data/processed",
        "data/checksums",
        "tests",
        "state/projects"
    ]
    
    logger.info("Creating project directory structure...")
    create_directories(project_root, required_dirs)
    
    logger.info("Project structure initialization complete.")

if __name__ == "__main__":
    main()
