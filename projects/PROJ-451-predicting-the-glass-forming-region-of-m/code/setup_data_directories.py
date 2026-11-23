"""
Script to ensure the standard data directory structure exists.
Creates data/raw, data/processed, data/interim, and data/results with .gitkeep files.
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

def create_directory_structure(base_path: Path) -> None:
    """
    Creates the required data directory structure and .gitkeep files.
    
    Args:
        base_path: The root project path (e.g., project root)
    """
    data_root = base_path / "data"
    
    directories = [
        "raw",
        "processed",
        "interim",
        "results"
    ]
    
    for dir_name in directories:
        dir_path = data_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            # Create a descriptive .gitkeep file
            description = f"# This directory stores {dir_name} data.\n# Do not delete this file."
            gitkeep_path.write_text(description)
            logger.info(f"Created {gitkeep_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")

def main():
    """Main entry point."""
    # Determine project root (assuming this script is in code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        create_directory_structure(project_root)
        logger.info("Data directory structure setup complete.")
    except Exception as e:
        logger.error(f"Failed to setup directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
