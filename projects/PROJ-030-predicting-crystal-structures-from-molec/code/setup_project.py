import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure we can import sibling modules if needed, though this script mostly uses stdlib
# The project root is expected to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-030-predicting-crystal-structures-from-molec"

# Directory structure to create
DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "data/models",
    "data/results",
    "data/validation",
    "data/figures",
    "logs",
    "tests",
    "docs",
    "specs",
    "figures",
    f"projects/{PROJECT_NAME}/code",
    f"projects/{PROJECT_NAME}/data/raw",
    f"projects/{PROJECT_NAME}/data/processed",
    f"projects/{PROJECT_NAME}/data/models",
    f"projects/{PROJECT_NAME}/data/results",
    f"projects/{PROJECT_NAME}/data/validation",
    f"projects/{PROJECT_NAME}/data/figures",
    f"projects/{PROJECT_NAME}/logs",
    f"projects/{PROJECT_NAME}/tests",
    f"projects/{PROJECT_NAME}/docs",
    f"projects/{PROJECT_NAME}/specs",
    f"projects/{PROJECT_NAME}/figures",
]

# Placeholder files to create (to ensure directories are not empty and structure is visible)
PLACEHOLDER_FILES = [
    ("code", ".gitkeep"),
    ("data/raw", ".gitkeep"),
    ("data/processed", ".gitkeep"),
    ("data/models", ".gitkeep"),
    ("data/results", ".gitkeep"),
    ("data/validation", ".gitkeep"),
    ("data/figures", ".gitkeep"),
    ("logs", ".gitkeep"),
    ("tests", ".gitkeep"),
    ("docs", ".gitkeep"),
    ("specs", ".gitkeep"),
    ("figures", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/code", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/data/raw", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/data/processed", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/data/models", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/data/results", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/data/validation", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/data/figures", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/logs", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/tests", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/docs", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/specs", ".gitkeep"),
    (f"projects/{PROJECT_NAME}/figures", ".gitkeep"),
]

def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

def create_placeholder_file(base_dir: Path, filename: str) -> None:
    """Create a .gitkeep placeholder file."""
    file_path = base_dir / filename
    if not file_path.exists():
        file_path.touch()
        print(f"Created placeholder: {file_path}")

def main() -> int:
    """Main entry point for project setup."""
    print(f"Setting up project structure for {PROJECT_NAME}...")
    print(f"Project Root: {PROJECT_ROOT}")

    # Create main directories
    for dir_name in DIRECTORIES:
        dir_path = PROJECT_ROOT / dir_name
        ensure_directory(dir_path)

    # Create placeholder files
    for base_dir_name, filename in PLACEHOLDER_FILES:
        base_path = PROJECT_ROOT / base_dir_name
        if base_path.exists():
            create_placeholder_file(base_path, filename)
        else:
            print(f"Warning: Base directory {base_path} does not exist, skipping placeholder.")

    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())