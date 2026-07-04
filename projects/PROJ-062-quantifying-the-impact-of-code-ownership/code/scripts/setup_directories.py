"""
Script to create the required directory structure for the project.
Creates data/raw, data/intermediate, data/results, tests/contract,
tests/integration, tests/unit, and docs directories.
"""
import os
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure under the given base path.
    
    Args:
        base_path: The root directory where the structure should be created.
    """
    directories = [
        "data/raw",
        "data/intermediate",
        "data/results",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def main() -> None:
    """Main entry point for the script."""
    # Determine the project root (parent of the 'code' directory)
    # Assuming this script is located at code/scripts/setup_directories.py
    script_dir = Path(__file__).resolve().parent
    code_dir = script_dir.parent
    project_root = code_dir.parent
    
    print(f"Project root: {project_root}")
    create_directories(project_root)
    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()