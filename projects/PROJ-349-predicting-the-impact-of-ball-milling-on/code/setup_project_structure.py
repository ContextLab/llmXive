"""
Project Structure Setup Script.

This script creates the required directory structure and placeholder files
for the llmXive automated science pipeline project.
"""
import os
import sys
from pathlib import Path


def setup_directories():
    """
    Create the project directory structure and placeholder files.

    Creates the following directories:
    - src/ (source code)
    - tests/ (test files)
    - data/raw (raw data)
    - data/processed (processed data)
    - data/splits (data splits)
    - results (model results and reports)
    - contracts/ (data contracts and schemas)
    - .github/workflows/ (CI/CD workflows)

    Adds .gitkeep files to ensure directories are tracked by git.
    """
    # Define the root directory (project root)
    root = Path(__file__).parent

    # Define all required directories
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows",
    ]

    # Create directories and .gitkeep files
    created_dirs = []
    for dir_name in directories:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Placeholder to keep directory in version control\n")
            created_dirs.append(str(dir_path))
        
        # Also create __init__.py for src and tests if they don't exist
        if dir_name in ["src", "tests"]:
            init_path = dir_path / "__init__.py"
            if not init_path.exists():
                init_path.write_text("# Package initialization\n")
                created_dirs.append(str(init_path))

    # Log results
    print(f"Project structure setup complete.")
    print(f"Created {len(created_dirs)} directories/files:")
    for item in created_dirs:
        print(f"  - {item}")
    
    return created_dirs


if __name__ == "__main__":
    setup_directories()
