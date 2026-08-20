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
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def create_directories(root: Path) -> None:
    """Creates the required directory structure for the project."""
    # Define all required directories relative to project root
    directories = [
        root / "code" / "analysis",
        root / "code" / "data_generation",
        root / "code" / "data_generation" / "utils",
        root / "code" / "model_training",
        root / "code" / "simulation",
        root / "code" / "tests" / "test_analysis",
        root / "code" / "tests" / "test_data_generation",
        root / "code" / "tests" / "test_model_training",
        root / "code" / "tests" / "test_simulation",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "data" / "models",
        root / "data" / "metrics",
        root / "data" / "analysis",
        root / "figures",
        root / "state" / "projects",
        root / "specs",
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path.relative_to(root)}")

def verify_structure(root: Path) -> bool:
    """Verifies that the required directory structure exists."""
    required_dirs = [
        "code",
        "code/analysis",
        "code/data_generation",
        "code/model_training",
        "code/simulation",
        "code/tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/models",
        "data/metrics",
        "data/analysis",
        "figures",
        "state/projects",
        "specs",
    ]

    missing = []
    for rel_path in required_dirs:
        full_path = root / rel_path
        if not full_path.is_dir():
            missing.append(rel_path)

    if missing:
        logger.error(f"Missing directories: {', '.join(missing)}")
        return False

    logger.info("All required directories verified.")
    return True

def main() -> int:
    """Main entry point for directory initialization."""
    try:
        root = get_project_root()
        logger.info(f"Project root: {root}")

        logger.info("Creating directory structure...")
        create_directories(root)

        logger.info("Verifying structure...")
        if not verify_structure(root):
            logger.error("Structure verification failed.")
            return 1

        logger.info("Directory initialization completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Error during initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
