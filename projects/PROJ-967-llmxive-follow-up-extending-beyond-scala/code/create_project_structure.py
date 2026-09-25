"""
Task T001a: Create project directory structure.
Creates the required directories for the llmXive follow-up project.
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

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def main() -> None:
    """Create the project directory structure."""
    # Define the project root relative to the repository root
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    # Define the required subdirectories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests",
    ]

    logger.info(f"Creating project structure in: {project_root}")
    
    for directory in directories:
        ensure_directory(directory)

    logger.info("Project directory structure creation completed.")

if __name__ == "__main__":
    main()
