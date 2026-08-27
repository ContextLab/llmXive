"""
Script to create the tests directory structure for the project.

This script creates the necessary directory hierarchy under the 'tests/'
directory to support unit, contract, and integration tests as defined
in the project plan.
"""
import os
import sys
from pathlib import Path

# Import project root configuration
# Assuming config.py is in the root of the 'code' directory or project root
# Adjusting import to work relative to this script's location
try:
    from config import PROJECT_ROOT
except ImportError:
    # Fallback if running directly without config import path setup
    _current = Path(__file__).resolve()
    _project_root = _current.parent.parent
    PROJECT_ROOT = _project_root
    sys.path.insert(0, str(_project_root))
    from config import PROJECT_ROOT

from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    else:
        logger.debug(f"Directory already exists: {path}")

def main() -> int:
    """
    Main function to create the tests directory structure.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    logger.info("Starting tests directory structure setup...")
    
    base_dir = Path(PROJECT_ROOT) / "tests"
    
    # Define the required directory structure
    # Based on tasks.md: tests/unit/, tests/contract/, tests/integration/
    dirs_to_create = [
        base_dir,
        base_dir / "unit",
        base_dir / "contract",
        base_dir / "integration",
        base_dir / "__pycache__", # Optional, but good practice to ensure structure
    ]
    
    success = True
    for dir_path in dirs_to_create:
        try:
            ensure_dir(dir_path)
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    if success:
        logger.info("Tests directory structure created successfully.")
        # List created structure for verification
        logger.info(f"Created structure under: {base_dir}")
        for root, dirs, _ in os.walk(base_dir):
            level = root.replace(str(base_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            logger.info(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for d in dirs:
                logger.info(f"{sub_indent}{d}/")
        return 0
    else:
        logger.error("Failed to create some directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
