"""
Project Structure Setup Script.

Creates the required directory structure for the llmXive automated science pipeline.
Ensures all necessary folders exist for data management, code organization, and CI/CD.
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

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "data/splits",
    "results",
    "contracts",
    ".github/workflows",
    "data/raw/materials_project",
    "data/raw/nist",
    "data/raw/arxiv",
    "data/processed/intermediate",
    "results/plots",
    "results/models",
    "src/ingest",
    "src/preprocess",
    "src/model",
    "src/evaluate",
    "src/interpret",
    "src/utils",
    "src/cli",
    "src/config",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def setup_directories(root_path: Path = None) -> bool:
    """
    Create all required directories for the project structure.

    Args:
        root_path: Optional path to use as project root. Defaults to current working directory.

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    if root_path is None:
        root_path = Path.cwd()

    logger.info(f"Setting up project structure in: {root_path}")

    success = True
    created_count = 0
    skipped_count = 0

    for dir_path in REQUIRED_DIRS:
        full_path = root_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
                skipped_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
        except Exception as e:
            logger.error(f"Unexpected error creating directory {full_path}: {e}")
            success = False

    logger.info(f"Setup complete. Created: {created_count}, Skipped: {skipped_count}")

    # Verification step
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        full_path = root_path / dir_path
        if not full_path.is_dir():
            missing_dirs.append(dir_path)

    if missing_dirs:
        logger.error(f"Verification failed. Missing directories: {missing_dirs}")
        return False

    logger.info("Verification passed. All required directories exist.")
    return True

def main():
    """Main entry point for the script."""
    # Determine project root (parent of the script directory)
    script_dir = Path(__file__).parent.resolve()
    # Try to find project root by looking for a marker file or going up
    # For now, assume script is in code/ and project root is parent
    project_root = script_dir.parent if script_dir.name == "code" else script_dir

    logger.info(f"Using project root: {project_root}")

    if setup_directories(project_root):
        logger.info("Project structure setup successful.")
        sys.exit(0)
    else:
        logger.error("Project structure setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()