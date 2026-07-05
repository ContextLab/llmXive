"""
Setup script to create the required directory structure for the project.

Creates:
- data/raw/
- data/processed/
- state/ (for checksums and intermediate state)

This script is idempotent and will not error if directories already exist.
"""
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories(base_path: Path) -> None:
    """
    Create the required directory structure under the given base path.
    
    Args:
        base_path: The root directory where the structure will be created.
    """
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "state",
    ]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.debug(f"Directory already exists: {directory}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            logger.info(f"Created .gitkeep in: {directory}")

def main():
    """Entry point for the script."""
    # Determine the project root (assuming this script is in code/data/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    setup_directories(project_root)
    
    # Verify creation
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    state_dir = project_root / "state"
    
    if raw_dir.exists() and processed_dir.exists() and state_dir.exists():
        logger.info("Directory structure setup complete.")
    else:
        logger.error("Failed to create all required directories.")
        raise RuntimeError("Directory creation failed.")

if __name__ == "__main__":
    main()
