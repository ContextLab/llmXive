import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> bool:
    """
    Creates a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    try:
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {p}")
        else:
            logger.info(f"Directory already exists: {p}")
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results"
    ]

    success = True
    for d in directories:
        if not ensure_directory(str(d)):
            success = False

    if success:
        logger.info("All required directories created successfully.")
    else:
        logger.error("Some directories failed to create.")
        sys.exit(1)

if __name__ == "__main__":
    main()