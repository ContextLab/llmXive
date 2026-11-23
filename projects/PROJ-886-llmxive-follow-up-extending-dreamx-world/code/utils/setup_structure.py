import os
import logging
from pathlib import Path

def main():
    """
    Initialize the full nested directory tree for PROJ-886-llmxive-follow-up-extending-dreamx-world.
    Creates the following directories relative to the project root:
    - data/raw/
    - data/derived/
    - data/derived/videos/
    - code/
    - code/models/
    - code/pipeline/
    - code/analysis/
    - code/utils/
    - tests/unit/
    - tests/integration/
    - logs/
    - docs/
    - config/
    """
    # Define the project root directory
    # We assume the script is run from the project root or that the path is relative to it
    project_root = Path("projects/PROJ-886-llmxive-follow-up-extending-dreamx-world")
    
    # Define the list of directories to create
    directories = [
        "data/raw",
        "data/derived",
        "data/derived/videos",
        "code",
        "code/models",
        "code/pipeline",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "logs",
        "docs",
        "config"
    ]

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Create the project root directory if it doesn't exist
    project_root.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured project root exists: {project_root}")

    # Create each subdirectory
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_path}")

    logger.info("Project structure initialization complete.")
    return 0

if __name__ == "__main__":
    main()
