"""
Script to initialize the project directory structure for PROJ-324.
This ensures all required folders (code, tests, data/raw, data/processed, data/derived)
exist before running the pipeline.
"""
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Define the project root relative to where this script runs
    # Assuming this script is run from the project root or the project root is its parent
    project_root = Path(__file__).parent / "projects" / "PROJ-324-predicting-molecular-properties-from-ope"
    
    # Define required directories
    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "derived",
        # Add standard support dirs if not already covered by existing files
        project_root / "figures",
        project_root / "docs",
    ]

    logger.info(f"Ensuring directory structure exists at: {project_root}")

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    # Create .gitkeep files to ensure empty directories are tracked by git
    gitkeep_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "derived",
        project_root / "figures",
        project_root / "docs",
    ]
    
    for dir_path in gitkeep_dirs:
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            logger.info(f"Created .gitkeep in: {dir_path}")

    logger.info(f"Setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()