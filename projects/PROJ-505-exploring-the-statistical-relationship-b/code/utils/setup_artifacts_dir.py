"""
Script to create the data/artifacts directory structure.
This satisfies task T010.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is in the path if running as a script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.mkdirs import ensure_dirs
from utils.logging import get_logger

logger = get_logger(__name__)

def main():
    """
    Creates the data/artifacts directory if it doesn't exist.
    """
    artifacts_dir = project_root / "data" / "artifacts"
    
    logger.info(f"Ensuring artifacts directory exists: {artifacts_dir}")
    
    # Use the existing ensure_dirs utility to create the directory
    # This handles creation of the full path if needed
    ensure_dirs([artifacts_dir])
    
    if artifacts_dir.exists() and artifacts_dir.is_dir():
        logger.info(f"Successfully created/verified directory: {artifacts_dir}")
        return 0
    else:
        logger.error(f"Failed to create directory: {artifacts_dir}")
        return 1

if __name__ == "__main__":
    sys.exit(main())