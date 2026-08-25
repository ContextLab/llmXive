"""
Setup script to create the docs/ directory for the project.
Verifies directory creation using pathlib as per task requirements.
"""
import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

def setup_docs_directory(root_dir: Optional[Path] = None) -> bool:
    """
    Create the docs/ directory if it doesn't exist.

    Args:
        root_dir: Optional root directory. Defaults to project root (parent of this file's parent).

    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    if root_dir is None:
        # Default to project root: parent of code/ directory
        root_dir = Path(__file__).parent.parent

    docs_path = root_dir.joinpath('docs')

    if docs_path.is_dir():
        logger.info(f"docs/ directory already exists at {docs_path}")
        return True

    try:
        docs_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created docs/ directory at {docs_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create docs/ directory at {docs_path}: {e}")
        return False

def verify_docs_directory(root_dir: Optional[Path] = None) -> bool:
    """
    Verify that the docs/ directory exists using pathlib.

    Args:
        root_dir: Optional root directory. Defaults to project root.

    Returns:
        True if docs/ exists, False otherwise.
    """
    if root_dir is None:
        root_dir = Path(__file__).parent.parent

    docs_path = root_dir.joinpath('docs')
    exists = docs_path.is_dir()

    if exists:
        logger.info(f"Verification passed: docs/ directory exists at {docs_path}")
    else:
        logger.error(f"Verification failed: docs/ directory does not exist at {docs_path}")

    return exists

def main() -> int:
    """
    Main entry point to create and verify the docs/ directory.

    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting docs/ directory setup...")

    # Create the directory
    created = setup_docs_directory()
    if not created:
        logger.error("Failed to create docs/ directory.")
        return 1

    # Verify the directory exists
    verified = verify_docs_directory()
    if not verified:
        logger.error("Verification failed: docs/ directory not found after creation.")
        return 1

    logger.info("docs/ directory setup and verification completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())