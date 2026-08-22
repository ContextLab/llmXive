"""
Setup script to create the complete directory structure for the project.
This script ensures all required folders for code, tests, data, and results exist.
"""
import os
from pathlib import Path
import sys

# Add the project root to the path to import config if needed, 
# though we can also derive paths relative to this script's location.
# Assuming this script is run from the project root or 'code' directory.

# Define the project root relative to this script (assuming script is in code/)
# If running as python code/setup_project_structure.py from root:
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Define the specific project directory name as per tasks.md
PROJECT_NAME = "PROJ-713-calibration-of-predictive-intervals-for-"
PROJECT_BASE = PROJECT_ROOT / PROJECT_NAME

# Define required directories
DIRS = [
    PROJECT_BASE / "code",
    PROJECT_BASE / "code" / "models",
    PROJECT_BASE / "code" / "metrics",
    PROJECT_BASE / "code" / "evaluation",
    PROJECT_BASE / "code" / "calibration",
    PROJECT_BASE / "code" / "utils",
    PROJECT_BASE / "tests",
    PROJECT_BASE / "tests" / "unit",
    PROJECT_BASE / "tests" / "contract",
    PROJECT_BASE / "tests" / "integration",
    PROJECT_BASE / "data" / "raw",
    PROJECT_BASE / "data" / "processed",
    PROJECT_BASE / "results",
    PROJECT_BASE / "results" / "figures",
    PROJECT_BASE / "specs",
]

def ensure_dir(path: Path):
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory exists: {path}")

def main():
    print(f"Setting up project structure at: {PROJECT_BASE}")
    if not PROJECT_BASE.exists():
        PROJECT_BASE.mkdir(parents=True, exist_ok=True)
        print(f"Created project root: {PROJECT_BASE}")
    
    for dir_path in DIRS:
        ensure_dir(dir_path)
    
    print("Project directory structure setup complete.")

if __name__ == "__main__":
    main()
