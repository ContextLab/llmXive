"""
Setup script to initialize the code/ directory structure for the llmXive project.
Creates subdirectories: data_generation, models, simulation, analysis.
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

def get_project_root() -> Path:
    """
    Returns the project root directory (parent of the 'code' directory).
    Assumes this script is located at code/setup_code_structure.py
    """
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def create_directories(root: Path) -> None:
    """
    Creates the required directory structure under code/.
    """
    code_dir = root / "code"
    subdirs = ["data_generation", "models", "simulation", "analysis"]

    for subdir in subdirs:
        dir_path = code_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

    # Ensure __init__.py files exist to make them packages
    for subdir in subdirs:
        init_file = code_dir / subdir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py in: {code_dir / subdir}")

def verify_structure(root: Path) -> bool:
    """
    Verifies that all required directories and __init__.py files exist.
    Returns True if structure is valid, False otherwise.
    """
    code_dir = root / "code"
    required_dirs = ["data_generation", "models", "simulation", "analysis"]
    all_valid = True

    logger.info("Verifying directory structure...")

    for subdir in required_dirs:
        dir_path = code_dir / subdir
        if not dir_path.is_dir():
            logger.error(f"Missing directory: {dir_path}")
            all_valid = False
        else:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                logger.warning(f"Missing __init__.py in: {dir_path}")
                # We created them in create_directories, so this shouldn't happen
            else:
                logger.info(f"Verified: {dir_path}")

    return all_valid

def main() -> int:
    """
    Main entry point for the setup script.
    Returns 0 on success, 1 on failure.
    """
    try:
        root = get_project_root()
        logger.info(f"Project root detected at: {root}")

        # Create directories
        create_directories(root)

        # Verify structure
        if verify_structure(root):
            logger.info("Directory structure initialization completed successfully.")
            return 0
        else:
            logger.error("Directory structure verification failed.")
            return 1

    except Exception as e:
        logger.exception(f"An error occurred during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())