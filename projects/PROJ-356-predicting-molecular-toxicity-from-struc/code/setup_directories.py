"""
Script to create the standard project directory structure.
This script ensures all required directories exist before pipeline execution.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard directory structure."""
    # Determine project root relative to this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent  # Go up to projects/PROJ-356...
    
    # Define relative paths to create under the project root
    # Note: We use the structure defined in tasks.md
    directories = [
        "code/src",
        "code/tests",
        "code/data",
        "code/results",
        "code/models",
        "code/config",
        "docs"
    ]

    created = []
    for rel_path in directories:
        target = project_root / rel_path
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(str(target))
        else:
            print(f"Directory already exists: {target}")

    # Ensure __init__.py files exist in Python packages
    init_files = [
        project_root / "code" / "src" / "__init__.py",
        project_root / "code" / "tests" / "__init__.py",
        project_root / "code" / "models" / "__init__.py",
        project_root / "code" / "config" / "__init__.py",
        project_root / "code" / "data" / "__init__.py",
        project_root / "code" / "results" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            created.append(str(init_file))

    print(f"Directory setup complete. Created {len(created)} items.")
    for item in created:
        print(f"  - {item}")

    return 0

if __name__ == "__main__":
    sys.exit(main())