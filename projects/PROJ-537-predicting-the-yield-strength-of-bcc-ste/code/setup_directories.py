"""
Setup script to create the required project directory structure.
This script ensures all necessary directories for data, code, tests, and provenance exist.
"""
import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/intermediate",
    "data/processed",
    "data/provenance",
    "data/results",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def create_directories(base_path: Path) -> None:
    """
    Create all required directories if they do not exist.

    Args:
        base_path: The root directory from which paths are resolved.
    """
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

def main() -> int:
    """
    Main entry point for the directory setup script.
    """
    # Determine the project root (assuming this script is in code/ or root)
    # We look for the 'data' or 'tests' directory to find the root, or assume cwd is root.
    # Based on the task, we assume the script is run from the project root or code/
    current_file = Path(__file__).resolve()
    
    # If running from code/, go up one level to project root
    if current_file.parent.name == "code":
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent

    print(f"Project root detected at: {project_root}")
    create_directories(project_root)
    
    # Verify creation
    missing = []
    for dir_path in REQUIRED_DIRS:
        if not (project_root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"Error: Failed to create the following directories: {missing}", file=sys.stderr)
        return 1
    
    print("All required directories created successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())