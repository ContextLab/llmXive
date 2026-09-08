import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists. Create it if it doesn't.

    Args:
        path: The Path object representing the directory to create.
    """
    if not path.exists():
        logger.info(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
    else:
        logger.debug(f"Directory already exists: {path}")


def main() -> None:
    """
    Main entry point for creating the project directory structure.
    Creates the required directories for the llmXive follow-up project.
    """
    # Define the base project path relative to the repository root
    # Assuming the script is run from the repository root
    base_path = Path.cwd()
    project_root = base_path / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

    # Define required subdirectories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests",
        # Additional directories mentioned in tasks.md for completeness
        project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "contracts",
        project_root / "venv",
    ]

    logger.info(f"Project root identified at: {project_root}")

    # Create all required directories
    for directory in directories:
        ensure_directory(directory)

    logger.info("All required project directories created successfully.")


if __name__ == "__main__":
    main()