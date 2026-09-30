"""
Script to initialize the project directory structure for PROJ-534.
Creates required directories for data, logs, tests, and source code.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (assuming code/ is the root for this implementation)
    # The task requires directories at repository root. 
    # Based on the API surface, 'code/' acts as the project root for the Python modules.
    # We will create the structure relative to the script's location or the 'code' directory.
    # To satisfy "repository root" relative to the project context (which seems to be `code/` based on imports),
    # we will create them in `code/` if the script is run from there, or adjust.
    
    # Let's assume the script is run from the project root (code/).
    # If running from `code/scripts/`, we go up one level.
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "logs",
        "contracts", # Needed for T003/T004 schema files
        "figures"    # Needed for T026
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # Create __init__.py files to make them packages
    init_files = [
        project_root / "src",
        project_root / "tests",
        project_root / "src" / "analysis",
        project_root / "src" / "data",
        project_root / "src" / "utils",
        project_root / "src" / "viz",
        project_root / "src" / "power",
        project_root / "src" / "sensitivity",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]

    for init_path in init_files:
        init_file = init_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
        else:
            print(f"Init file already exists: {init_file}")

    print(f"Setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()