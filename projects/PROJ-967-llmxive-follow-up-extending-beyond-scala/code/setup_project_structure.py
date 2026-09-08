"""
Setup script to create the project directory structure for llmXive.
Implements Task T001a.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

# Directories to create as per T001a
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "results",
    "code",
    "tests"
]

def ensure_directory(dir_path: Path) -> None:
    """Create a directory if it does not exist."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    else:
        logger.info(f"Directory already exists: {dir_path}")

def main() -> int:
    """Main entry point to create the project structure."""
    logger.info(f"Target project directory: {PROJECT_DIR}")

    # Ensure the base project directory exists
    ensure_directory(PROJECT_DIR)

    # Create all required subdirectories
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_DIR / dir_name
        ensure_directory(full_path)

    logger.info("Project directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
