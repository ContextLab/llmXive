"""
Project Structure Initialization Script.
Implements T001: Create project structure per implementation plan.
"""
import os
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_NAME = "PROJ-444-predicting-molecular-properties-from-top"
BASE_PATH = PROJECT_ROOT / "projects" / PROJECT_NAME

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/logs",
    "tests",
    "reports",
    "state"
]

README_CONTENT = "Project: Predicting Molecular Properties from TDA"

def ensure_directory(dir_path: Path) -> bool:
    """Create a directory if it does not exist."""
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
        return False

def initialize_readme(base_path: Path) -> bool:
    """Create the README.md file with the specified content."""
    readme_path = base_path / "README.md"
    try:
        readme_path.write_text(README_CONTENT, encoding="utf-8")
        return True
    except OSError as e:
        print(f"Error creating README.md: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point for project structure initialization."""
    print(f"Initializing project structure at: {BASE_PATH}")
    
    # Create base project directory
    if not ensure_directory(BASE_PATH):
        sys.exit(1)

    # Create required subdirectories
    success = True
    for dir_name in REQUIRED_DIRS:
        dir_path = BASE_PATH / dir_name
        if not ensure_directory(dir_path):
            success = False
            print(f"Failed to create: {dir_path}")

    if not success:
        print("Project structure initialization failed.", file=sys.stderr)
        sys.exit(1)

    # Create README.md
    if not initialize_readme(BASE_PATH):
        sys.exit(1)

    # Verification
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        if not (BASE_PATH / dir_name).exists():
            missing_dirs.append(dir_name)

    if missing_dirs:
        print(f"Verification failed: Missing directories {missing_dirs}", file=sys.stderr)
        sys.exit(1)

    if not (BASE_PATH / "README.md").exists():
        print("Verification failed: README.md missing", file=sys.stderr)
        sys.exit(1)

    readme_text = (BASE_PATH / "README.md").read_text(encoding="utf-8")
    if not readme_text.strip():
        print("Verification failed: README.md is empty", file=sys.stderr)
        sys.exit(1)

    print("Project structure created successfully.")
    print(f"  - Directories: {', '.join(REQUIRED_DIRS)}")
    print(f"  - README.md: '{README_CONTENT}'")

if __name__ == "__main__":
    main()