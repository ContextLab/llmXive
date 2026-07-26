"""
Script to create the required data directory structure for the project.
Creates data/raw/ and data/processed/ directories as specified in T004a.
"""
import os
import sys
from pathlib import Path
import logging

# Configure basic logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_data_directories(base_path: Optional[Path] = None) -> bool:
    """
    Create the required data directory structure.

    Args:
        base_path: Base path for the project. If None, uses current working directory.

    Returns:
        True if all directories were created successfully, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()

    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/config",
        "state",
        "output",
        "logs",
        "docs/paper",
        "docs/reports",
    ]

    success = True
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False

    # Verify the specific directories for T004a
    raw_dir = base_path / "data" / "raw"
    processed_dir = base_path / "data" / "processed"

    if not raw_dir.exists() or not processed_dir.exists():
        logger.error("Critical: data/raw or data/processed directories missing")
        return False

    logger.info("Data directory structure created successfully.")
    return True


def main() -> int:
    """Main entry point for the script."""
    logger.info("Starting directory creation for T004a...")

    # Determine project root (assuming script is in code/utils/)
    # We look for the 'code' directory to find the root
    current_path = Path(__file__).resolve()
    project_root = current_path.parent.parent

    logger.info(f"Project root detected at: {project_root}")

    success = create_data_directories(project_root)

    if success:
        logger.info("T004a verification passed: data/raw and data/processed exist.")
        return 0
    else:
        logger.error("T004a verification failed: directories could not be created.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
