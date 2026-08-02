"""
Setup script for creating the required directory structure for the project.
Creates data/raw, data/processed, data/models, and logs directories.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories(base_path: str = ".") -> None:
    """
    Create the required directory structure under the base path.

    Directories to create:
    - data/raw
    - data/processed
    - data/models
    - logs

    Args:
        base_path: The root directory where the structure will be created.
    """
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "logs"
    ]

    base = Path(base_path)
    logger.info(f"Setting up directory structure under: {base.absolute()}")

    created_count = 0
    for dir_path in required_dirs:
        full_path = base / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {full_path}")

    logger.info(f"Setup complete. Created {created_count} new directories.")

def main() -> None:
    """Entry point for the script."""
    # Determine the project root (assuming script is in code/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    try:
        setup_directories(str(project_root))
        logger.info("Directory setup finished successfully.")
    except Exception as e:
        logger.error(f"Failed to setup directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()