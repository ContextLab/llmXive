import os
import sys
from pathlib import Path

def ensure_directory(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep file to ensure the directory is tracked by git
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# This file ensures the directory is tracked by git\n")
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def setup_project_structure() -> None:
    """Create the standard project directory structure."""
    project_root = Path(".")
    
    # Define directories to create
    directories = [
        "code",
        "code/ingestion",
        "code/features",
        "code/modeling",
        "code/screening",
        "code/reporting",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/processed",
        "data/reports",
        "artifacts",
        "figures"
    ]
    
    for dir_path in directories:
        ensure_directory(dir_path)
    
    print("Project directory structure setup complete.")

def main():
    """Main entry point for directory setup."""
    setup_project_structure()

if __name__ == "__main__":
    main()