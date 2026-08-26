import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent

def create_directories() -> None:
    """Create the required project directory structure."""
    project_root = get_project_root()
    
    # Define directories to create
    directories = [
        "src",
        "tests",
        "specs/001-predicting-reaction-mechanisms",
        "data",
        "state/projects",
        # Additional standard directories for a complete project structure
        "src/utils",
        "src/ingestion",
        "src/modeling",
        "src/analysis",
        "src/scripts",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/reference",
        "data/results",
        "figures",
        "specs/contracts",
        "state/projects",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def main() -> None:
    """Main entry point for project setup."""
    print("Setting up project directory structure...")
    create_directories()
    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()
