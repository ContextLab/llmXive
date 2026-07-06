"""
Data Directory Setup Module.

This module initializes the required directory structure for the project's
data management pipeline, specifically creating the 'raw' and 'processed'
data directories with .gitkeep placeholders to ensure they are tracked
by version control.
"""
import os
from pathlib import Path
import logging

# Configure local logger if not already configured in the main flow
logger = logging.getLogger(__name__)

def setup_data_directories(base_dir: Optional[Path] = None) -> None:
    """
    Creates the standard data directory structure: data/raw/ and data/processed/.
    
    Args:
        base_dir: Optional base directory. If None, uses the project root 
                  relative to this file's location or current working directory.
                  Defaults to 'data' relative to the project root.
    
    Raises:
        OSError: If directories cannot be created due to permissions or other OS errors.
    """
    if base_dir is None:
        # Determine project root: assume this file is in code/ relative to root
        # or just use current working directory if run from root
        base_dir = Path.cwd()
    
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    directories = [raw_dir, processed_dir]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise e
    
    # Create .gitkeep files to ensure directories are tracked by git
    # even if they are empty.
    gitkeep_content = "# This file ensures the directory is tracked by version control.\n"
    
    for directory in directories:
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            try:
                with open(gitkeep_path, "w", encoding="utf-8") as f:
                    f.write(gitkeep_content)
                logger.info(f"Created .gitkeep in {directory}")
            except OSError as e:
                logger.warning(f"Could not create .gitkeep in {directory}: {e}")
                # Do not raise here as the directory itself exists, 
                # but log the issue.

if __name__ == "__main__":
    # Basic execution script to run the setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    setup_data_directories()
    print("Data directories setup complete.")