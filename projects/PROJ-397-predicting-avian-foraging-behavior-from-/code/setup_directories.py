"""
Script to initialize the project directory structure for PROJ-397.
Creates the required folder hierarchy under code/.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the base directory for this project
    # The task specifies the project root as: projects/PROJ-397-predicting-avian-foraging-behavior-from-
    # However, the constraints state: "All artifact paths are relative to the project root and MUST live under code/..."
    # The task description asks to create: `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/{...}`
    # Since we are running this script from within the project context, we assume the current working directory
    # or a relative path `code/` is the target root for the subdirectories.
    # To be safe and compliant with "stay inside the project tree", we create these relative to the current directory
    # which represents the project root in the execution context.
    
    base_path = Path("code")
    
    # Ensure the base 'code' directory exists first
    base_path.mkdir(parents=True, exist_ok=True)
    
    subdirs = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        dir_path = base_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    # Also create __init__.py files in Python packages to ensure they are recognized
    # and to satisfy import requirements for sibling modules if any.
    # The task specifically asked for directories, but making them packages is best practice.
    # We will create __init__.py in data, models, viz, utils, tests.
    # notebooks is usually not a package.
    package_dirs = ["data", "models", "viz", "utils", "tests"]
    for pkg_dir in package_dirs:
        pkg_file = base_path / pkg_dir / "__init__.py"
        if not pkg_file.exists():
            pkg_file.touch()
            print(f"Created __init__.py in: {pkg_file}")
    
    print(f"Directory structure initialization complete for {base_path}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())