import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory (parent of the code/ directory)."""
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def create_directories() -> None:
    """Create the required project directory structure."""
    root = get_project_root()
    
    # Define directories to create based on T001a requirements
    directories = [
        root / "src",
        root / "tests",
        root / "specs" / "001-predicting-reaction-mechanisms",
        root / "data",
        root / "state" / "projects",
        # Additional subdirectories needed for the project structure
        root / "src" / "ingestion",
        root / "src" / "modeling",
        root / "src" / "analysis",
        root / "src" / "utils",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "data" / "reference",
        root / "state" / "projects" / "PROJ-088-predicting-reaction-mechanisms-from-spec",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory.relative_to(root)}")

def main() -> None:
    """Main entry point for project setup."""
    print("Setting up project directory structure...")
    create_directories()
    print("Project setup complete.")

if __name__ == "__main__":
    main()
