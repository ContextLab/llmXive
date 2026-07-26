"""
Data Directory Structure Setup Module.

This module provides functionality to initialize the required directory
structure for the project's data, outputs, and model artifacts.
It ensures that all necessary folders exist and are marked with .gitkeep
files to be tracked by version control.
"""
import os
from pathlib import Path
from typing import List

from config import PROJECT_ROOT
from utils.logger import get_logger


def setup_data_directories() -> List[str]:
    """
    Create the required data directory structure and .gitkeep files.

    Creates the following directories under the project root:
    - data/prompts/
    - data/models/
    - data/outputs/base/
    - data/outputs/rl_unified/
    - data/results/
    - data/reports/
    - figures/

    Each directory is initialized with a .gitkeep file to ensure
    version control tracking.

    Returns:
        List[str]: A list of paths to the created directories.
    """
    logger = get_logger(__name__)
    logger.info("Initializing data directory structure...")

    # Define the required directory paths relative to PROJECT_ROOT
    base_data_dir = PROJECT_ROOT / "data"
    
    required_dirs = [
        base_data_dir / "prompts",
        base_data_dir / "models",
        base_data_dir / "outputs" / "base",
        base_data_dir / "outputs" / "rl_unified",
        base_data_dir / "results",
        base_data_dir / "reports",
        PROJECT_ROOT / "figures",
    ]

    created_paths = []

    for dir_path in required_dirs:
        try:
            # Create directory with parents if they don't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep file to ensure directory is tracked
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.write_text(
                    "# This directory is tracked by git.\n"
                    "# Do not delete this file.\n"
                )
            
            created_paths.append(str(dir_path))
            logger.info(f"Created directory: {dir_path}")
            
        except PermissionError:
            logger.error(f"Permission denied creating directory: {dir_path}")
            raise
        except OSError as e:
            logger.error(f"OS error creating directory {dir_path}: {e}")
            raise

    logger.info(f"Successfully initialized {len(created_paths)} directories.")
    return created_paths


if __name__ == "__main__":
    # When run as a script, execute the setup
    setup_data_directories()
    print("Data directory structure setup complete.")