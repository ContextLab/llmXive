"""
Verification script for project directory structure.
Ensures all required directories created in T001a-T001g exist.
Fails loudly if any are missing.
"""
import os
import sys
import logging
from pathlib import Path

# Import project configuration utilities
from config import get_project_root, get_data_path, get_output_path

# Configure logging to output to console and file
def setup_verification_logging():
    """Setup basic logging for the verification script."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("outputs/verify_directories.log")
        ]
    )

def verify_directories():
    """
    Verify the existence of all directories created in T001a-T001g.
    Returns True if all exist, False otherwise.
    """
    setup_verification_logging()
    logger = logging.getLogger(__name__)
    
    project_root = get_project_root()
    logger.info(f"Verifying directories in project root: {project_root}")

    # List of required directories relative to project root
    # Based on T001a-T001g:
    # T001a: data/raw/
    # T001b: data/processed/
    # T001c: code/
    # T001d: outputs/
    # T001e: tests/
    # T001f: state/projects/
    # T001g: code/models/
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models"
    ]

    missing_dirs = []
    existing_dirs = []

    for dir_path in required_dirs:
        full_path = Path(project_root) / dir_path
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(dir_path)
            logger.info(f"✓ Found: {dir_path}")
        else:
            missing_dirs.append(dir_path)
            logger.error(f"✗ MISSING: {dir_path} (Expected at: {full_path})")

    logger.info(f"\nSummary: {len(existing_dirs)} found, {len(missing_dirs)} missing")

    if missing_dirs:
        logger.error("FATAL: Required directories are missing. Verification failed.")
        logger.error("Missing directories:")
        for d in missing_dirs:
            logger.error(f"  - {d}")
        return False
    else:
        logger.info("SUCCESS: All required directories verified.")
        return True

def main():
    """Entry point for the script."""
    success = verify_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
