import os
import sys
from pathlib import Path
import logging

def ensure_directory(dir_path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {path}")
    else:
        logging.info(f"Directory already exists: {path}")

def main() -> None:
    """Create the project directory structure for PROJ-967."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Define the base project root relative to repository root
    # Assuming this script runs from the repository root or code/ directory
    # We use relative paths as specified in the task description
    base_path = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")

    # Define required directories
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "results",
        base_path / "code",
        base_path / "tests",
    ]

    logging.info(f"Creating project structure at: {base_path}")

    for directory in directories:
        ensure_directory(str(directory))

    logging.info("Project directory structure creation complete.")

if __name__ == "__main__":
    main()
