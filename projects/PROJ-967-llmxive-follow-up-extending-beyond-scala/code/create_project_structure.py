import os
import sys
from pathlib import Path
import logging

def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {path}")
    else:
        logging.debug(f"Directory already exists: {path}")

def main():
    """Create the project directory structure for PROJ-967."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Define the project root relative to the repository root
    # Assuming the script is run from the repository root or code/ directory
    repo_root = Path(__file__).parent.parent
    project_root = repo_root / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests",
    ]

    for dir_path in directories:
        ensure_directory(dir_path)

    logging.info("Project directory structure created successfully.")

if __name__ == "__main__":
    main()