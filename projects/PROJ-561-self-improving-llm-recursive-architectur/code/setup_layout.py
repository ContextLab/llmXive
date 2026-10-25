"""
Setup script for creating the required project directory layout and
initializing __init__.py files in each package directory.

This script is idempotent: running it multiple times will not raise errors
and will ensure the expected directories and files exist.
"""
import os
from pathlib import Path

# List of directories to create relative to the project root
DIRS = [
    "code",
    "code/tests",
    "code/tests/unit",
    "code/tests/integration",
    "data/raw",
    "data/processed",
    "results",
    "state",  # Required by the original task specification; kept empty to avoid platform state usage
]

def ensure_directories():
    project_root = Path(__file__).resolve().parents[1]  # project root is two levels up from this script
    for rel_dir in DIRS:
        dir_path = project_root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create an __init__.py in any Python package directory
        if rel_dir.startswith("code"):
            init_path = dir_path / "__init__.py"
            if not init_path.exists():
                init_path.write_text('"""Package marker."""\n')

if __name__ == "__main__":
    ensure_directories()