import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-455.
    This script ensures all necessary folders for code, data, tests, and contracts exist.
    """
    # Define the base directory relative to the script location or current working directory
    # The task specifies creating under the project root. We assume the script runs from the project root
    # or we calculate the root relative to this file if it's inside a 'code' folder.
    # Based on the task description, we are creating:
    # code/data, code/models, code/analysis, tests/unit, tests/integration, tests/contract, tests/benchmark,
    # contracts, data/raw, data/processed, data/results.
    
    # We assume the script is located in 'code/setup_project.py'
    # So the project root is the parent of 'code'
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    dirs_to_create = [
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "analysis",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "tests" / "benchmark",
        project_root / "contracts",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())