"""
Script to create the required project directory structure for the pipeline.
This implements task T001: "Create project structure per implementation plan".
It can be executed directly via:
    python code/create_structure.py
The script is idempotent and will not raise an error if directories already exist.
"""

import sys
from pathlib import Path

def create_directories():
    # List of directories to create relative to the repository root
    dirs = [
        "code/data",
        "code/analysis",
        "code/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/derived",
        "state/projects",
    ]

    repo_root = Path(__file__).resolve().parent.parent
    for rel_path in dirs:
        dir_path = repo_root / rel_path
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created (or already existed): {dir_path}")
        except Exception as e:
            print(f"Failed to create {dir_path}: {e}", file=sys.stderr)
            raise

if __name__ == "__main__":
    create_directories()
    print("Project directory structure has been created successfully.")