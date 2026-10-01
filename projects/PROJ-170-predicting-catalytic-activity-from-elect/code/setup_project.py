import os
import sys
import logging
from pathlib import Path
from config import get_project_root

def setup_verification_logging():
    """Initialize logging for verification steps."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def create_directories(project_root: Path, logger: logging.Logger):
    """Create the required project directory structure."""
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "outputs",
        project_root / "tests",
        project_root / "state" / "projects",
        project_root / "code" / "models"
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

def verify_directories(project_root: Path, logger: logging.Logger) -> bool:
    """Verify that all required directories exist."""
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "outputs",
        project_root / "tests",
        project_root / "state" / "projects",
        project_root / "code" / "models"
    ]

    all_exist = True
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            logger.error(f"Directory missing: {dir_path}")
            all_exist = False
        else:
            logger.info(f"Verified directory exists: {dir_path}")

    return all_exist

def create_init_files(project_root: Path, logger: logging.Logger):
    """Create __init__.py files in Python package directories."""
    package_dirs = [
        project_root / "code",
        project_root / "tests",
        project_root / "code" / "utils",
        project_root / "code" / "models"
    ]

    for dir_path in package_dirs:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logger.info(f"Created __init__.py: {init_file}")

def main():
    """Main entry point for project setup."""
    logger = setup_verification_logging()
    logger.info("Starting project directory setup...")

    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    # Create directories
    create_directories(project_root, logger)

    # Verify directories
    if not verify_directories(project_root, logger):
        logger.error("Directory initialization failed")
        sys.exit(1)

    # Create __init__.py files
    create_init_files(project_root, logger)

    logger.info("Project setup completed successfully")

if __name__ == "__main__":
    main()
