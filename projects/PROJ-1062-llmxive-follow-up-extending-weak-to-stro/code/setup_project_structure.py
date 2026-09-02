"""
Script to initialize the project directory structure for llmXive follow-up.
Creates all required directories under the project root as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the script location or current working directory
    # The script is expected to be run from the project root or code directory
    current_dir = Path(__file__).parent
    project_root = current_dir.parent if current_dir.name == "code" else current_dir

    # Define the relative paths to create
    # Based on tasks.md T001 requirements
    directories = [
        "code/src/data",
        "code/src/models",
        "code/src/training",
        "code/src/analysis",
        "code/src/config",
        "code/tests/unit",
        "code/tests/integration",
        "code/contracts",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "code/artifacts",
        # Additional standard directories often needed for a full pipeline
        "code/src/core",
        "code/src/scripts",
        "docs",
        "data/figures"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure at: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            skipped_count += 1
            continue
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            # Create __init__.py in Python package directories to ensure they are recognized as packages
            if "src" in dir_path or "tests" in dir_path or "code" in dir_path:
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
            created_count += 1
            print(f"Created: {full_path}")
        except PermissionError:
            print(f"Permission denied creating: {full_path}")
        except Exception as e:
            print(f"Error creating {full_path}: {e}")

    print(f"\nProject structure initialization complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {skipped_count}")

    return 0

if __name__ == "__main__":
    sys.exit(main())