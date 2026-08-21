import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory (parent of this script)."""
    return Path(__file__).resolve().parent

def create_directories(project_root: Path) -> None:
    """Create the required project directory structure."""
    required_dirs = [
        "src",
        "tests",
        "specs/001-predicting-reaction-mechanisms",
        "data",
        "state/projects",
        # Additional standard directories for completeness
        "data/raw",
        "data/processed",
        "data/reference",
        "data/results",
        "figures",
        "state",
        "specs/contracts",
        "src/utils",
        "src/ingestion",
        "src/modeling",
        "src/analysis",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path.relative_to(project_root)}")

def main() -> None:
    """Main entry point for project setup."""
    project_root = get_project_root()
    print(f"Setting up project structure in: {project_root}")
    create_directories(project_root)
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()