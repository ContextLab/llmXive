"""
Project Structure Initialization for llmXive - Dynamic Socio-Cognitive State Injection.

This module creates the required directory structure for the research pipeline,
ensuring all necessary folders exist before data generation and experiment execution.
"""

import os
import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_directory_structure(root_path: Optional[Path] = None) -> List[Path]:
    """
    Creates the required directory structure for the project.

    Args:
        root_path: The root directory for the project. Defaults to current working directory.

    Returns:
        List[Path]: A list of created directory paths.
    """
    if root_path is None:
        root_path = Path.cwd()

    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "contracts"
    ]

    created_paths = []

    logger.info(f"Initializing project structure at: {root_path}")

    for dir_name in required_dirs:
        full_path = root_path / dir_name
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            else:
                logger.info(f"Directory already exists: {full_path}")
            created_paths.append(full_path)
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

    # Create __init__.py files to make directories Python packages where appropriate
    init_files = []
    for dir_path in created_paths:
        if dir_path.name in ["code", "tests"]:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                logger.info(f"Created package marker: {init_file}")
                init_files.append(init_file)

    logger.info("Project structure initialization complete.")
    return created_paths


def main():
    """
    Main entry point for the directory structure creation script.
    """
    try:
        created_dirs = create_directory_structure()
        print("\nSuccessfully created the following directories:")
        for d in created_dirs:
            print(f"  - {d}")
        print("\nProject structure is ready for implementation.")
    except Exception as e:
        print(f"Error during directory creation: {e}")
        raise


if __name__ == "__main__":
    main()
