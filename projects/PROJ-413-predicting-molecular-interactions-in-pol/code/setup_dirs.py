import os
import sys
from pathlib import Path

def main():
    """Create project directory structure per implementation plan."""
    project_root = Path(__file__).parent.parent
    project_name = "PROJ-413-predicting-molecular-interactions-in-pol"
    project_path = project_root / project_name

    if not project_path.exists():
        project_path.mkdir(parents=True)
        print(f"Created project root: {project_path}")

    # Define directories to create relative to project root
    dirs = [
        "data/raw",
        "data/curated",
        "data/processed",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "results",
        "analysis",
        "docs",
        "tests/contract",
        "tests/integration",
    ]

    created_count = 0
    for dir_path in dirs:
        full_path = project_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True)
            created_count += 1
            print(f"Created directory: {full_path.relative_to(project_path)}")
        else:
            print(f"Directory exists: {full_path.relative_to(project_path)}")

    print(f"\nProject structure initialized at: {project_path}")
    print(f"Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
