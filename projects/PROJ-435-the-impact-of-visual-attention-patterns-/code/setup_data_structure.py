import os
import sys
import logging
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """Get the project root directory (parent of 'code' directory)."""
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def setup_logging() -> None:
    """Configure basic logging for the project."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories(root: Path, directories: List[str]) -> None:
    """Create the specified directory structure."""
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {full_path}")

def main() -> None:
    """Main entry point to initialize project structure."""
    setup_logging()
    root = get_project_root()
    logging.info(f"Project root: {root}")

    # Define the required directory structure per implementation plan
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "data/processed",
        "tests",
        "state",
        "output",
        "figures",
        "scripts"
    ]

    create_directories(root, directories)
    logging.info("Project structure initialization complete.")

if __name__ == "__main__":
    main()
