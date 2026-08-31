import os
import sys
from pathlib import Path
import logging

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Assuming this file is at code/setup_code_structure.py, root is parent of parent
    return current.parent.parent

def create_directories() -> bool:
    """
    Initialize the `code/` directory structure.
    Returns True if successful, False otherwise.
    """
    root = get_project_root()
    code_dir = root / "code"

    if code_dir.exists():
        logging.info(f"Directory {code_dir} already exists.")
        return True

    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Successfully created directory: {code_dir}")
        return True
    except OSError as e:
        logging.error(f"Failed to create directory {code_dir}: {e}")
        return False

def verify_structure() -> bool:
    """
    Verify that the `code/` directory exists.
    """
    root = get_project_root()
    code_dir = root / "code"
    if code_dir.exists() and code_dir.is_dir():
        logging.info("Verification passed: code/ directory exists.")
        return True
    else:
        logging.error("Verification failed: code/ directory does not exist.")
        return False

def main():
    """Main entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info("Starting code directory initialization...")
    success = create_directories()
    if success:
        success = verify_structure()

    if success:
        logging.info("Task T001a completed successfully.")
        return 0
    else:
        logging.error("Task T001a failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())