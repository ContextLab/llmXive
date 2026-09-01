import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-815-llmxive-follow-up-extending-intern-atlas.
    This script creates the required folders relative to the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-815-llmxive-follow-up-extending-intern-atlas"
    project_path = project_root / "projects" / project_name

    # Define the directory structure to create
    # Based on task description: mkdir -p projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/{code/data,code/models,code/analysis,code/utils,data/raw,data/processed,tests/unit,tests/integration}
    directories = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        except PermissionError:
            print(f"Permission denied creating directory: {full_path}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return 1

    if created_count == len(directories):
        print(f"Successfully created {created_count} directories under {project_path}")
        return 0
    else:
        print(f"Completed with some errors. Created {created_count} out of {len(directories)} directories.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())