import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def setup_data_directories(base_path: Path) -> None:
    """
    Create the required data directory structure:
    - data/raw
    - data/processed

    Args:
        base_path: The root directory of the project.
    """
    raw_dir = base_path / "data" / "raw"
    processed_dir = base_path / "data" / "processed"

    directories = [raw_dir, processed_dir]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")


def create_gitignore(base_path: Path) -> None:
    """
    Create or update the .gitignore file to ignore large data files.
    Ensures data directories are ignored while keeping the .gitkeep files.

    Args:
        base_path: The root directory of the project.
    """
    gitignore_path = base_path / ".gitignore"
    
    # Content to add for data directories
    gitignore_content = """
    # Data directories - ignore large files
    data/raw/
    data/processed/
    
    # Keep the directory structure
    data/raw/.gitkeep
    data/processed/.gitkeep
    """

    # Read existing content if file exists
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()
        logger.info(f"Existing .gitignore found at {gitignore_path}")
    
    # Check if we need to add the data rules
    if "data/raw/" not in existing_content:
        with open(gitignore_path, "a") as f:
            f.write(gitignore_content)
        logger.info(f"Updated .gitignore at {gitignore_path}")
    else:
        logger.info(".gitignore already contains data directory rules")


def main() -> None:
    """
    Main entry point to setup data directory structure and .gitignore.
    """
    # Determine the project root (assuming this script is in code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    logger.info(f"Project root: {project_root}")
    
    # Setup directories
    setup_data_directories(project_root)
    
    # Create .gitignore
    create_gitignore(project_root)
    
    # Create .gitkeep files to ensure directories are tracked by git
    (project_root / "data" / "raw" / ".gitkeep").touch()
    (project_root / "data" / "processed" / ".gitkeep").touch()
    
    logger.info("Data directory structure setup complete.")


if __name__ == "__main__":
    main()