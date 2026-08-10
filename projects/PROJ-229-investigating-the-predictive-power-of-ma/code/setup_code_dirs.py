"""
Setup script to create the required code subdirectories.
This implements task T001b.
"""
import os
import logging
from pathlib import Path
from typing import List

# Import logger utility from the existing API surface
from code.utils.logger import get_pipeline_logger

# Import config to determine project root if needed, though we assume standard structure
from config import get_config

def create_code_directories(base_path: Path) -> List[Path]:
    """
    Creates the required code subdirectories: data, models, utils.

    Args:
        base_path: The root directory of the project.

    Returns:
        A list of Path objects for the created directories.
    """
    code_dirs = [
        "code/data",
        "code/models",
        "code/utils"
    ]

    created_paths = []
    logger = get_pipeline_logger()

    for dir_str in code_dirs:
        target_path = base_path / dir_str
        try:
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
            else:
                logger.info(f"Directory already exists: {target_path}")
            created_paths.append(target_path)
        except OSError as e:
            logger.error(f"Failed to create directory {target_path}: {e}")
            raise

    return created_paths

def main():
    """
    Entry point for the script.
    Creates directories relative to the project root.
    """
    # Determine project root. Assuming this script is in code/ or root.
    # We look for the config.yaml or data/ to find the root.
    current_file = Path(__file__).resolve()
    
    # Heuristic: find the directory containing 'config.yaml' or 'data/'
    # Usually the project root is the parent of 'code'
    project_root = current_file.parent.parent if current_file.name.startswith("setup_") else current_file.parent
    
    # If running from code/setup_code_dirs.py, root is parent of code
    if (project_root / "code").exists() and (project_root / "config.yaml").exists():
        pass # project_root is correct
    elif (current_file.parent / "config.yaml").exists():
        project_root = current_file.parent
    else:
        # Fallback to current working directory if structure is ambiguous
        project_root = Path.cwd()

    logging.basicConfig(level=logging.INFO)
    logger = get_pipeline_logger()
    logger.info(f"Project root detected at: {project_root}")

    create_code_directories(project_root)
    logger.info("Code directory setup complete.")

if __name__ == "__main__":
    main()
