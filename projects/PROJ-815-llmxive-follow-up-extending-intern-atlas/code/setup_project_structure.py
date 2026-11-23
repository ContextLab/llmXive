"""
Script to initialize the project directory structure for PROJ-815-llmxive-follow-up-extending-intern-atlas.
Creates all required directories under the project root as specified in T001.
"""
import os
import sys
from pathlib import Path


def main():
    # Determine the project root.
    # We assume this script is located at: <repo_root>/code/setup_project_structure.py
    # The project root is the parent of 'code'.
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    # Define the specific project directory
    project_name = "PROJ-815-llmxive-follow-up-extending-intern-atlas"
    project_root = repo_root / "projects" / project_name

    # Define the required subdirectories relative to the project root
    # Note: 'code' and 'data' must be direct children of project_root, not nested.
    required_dirs = [
        "code/data",
        "code/utils",
        "code/models",
        "code/analysis",
        "data/raw",
        "data/processed",
        "data/cache",
        "tests/unit",
        "tests/integration",
        "paper/results",
        "state",
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Ensure the root project directory exists
    if not project_root.exists():
        project_root.mkdir(parents=True, exist_ok=True)
        print(f"Created project root: {project_root}")
        created_count += 1

    print(f"\nProject structure initialization complete.")
    print(f"Project root: {project_root}")
    print(f"Directories created: {created_count}")

    # Verify structure
    print("\nVerifying structure:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [MISSING] {dir_path}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())