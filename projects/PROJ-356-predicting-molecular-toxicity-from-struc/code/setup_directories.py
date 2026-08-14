import os
import sys
from pathlib import Path

def main():
    """
    Creates the root project directory structure for PROJ-356.
    This script ensures that the required directories exist under the code/ folder.
    """
    # Define the base project root relative to this script's location
    # Assuming this script is at: code/setup_directories.py
    # The project root is the parent of 'code'
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent

    # Define the required directories relative to the code directory
    # The task requires: projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/
    # Since we are running inside that code directory, we just ensure subdirs exist.
    
    required_dirs = [
        "src",
        "tests",
        "data",
        "results",
        "models",
        "config",
        "scripts",
        "features",
        "evaluation",
        "utils"
    ]

    print(f"Project Root: {project_root}")
    print(f"Code Directory: {code_dir}")

    created_count = 0
    for dir_name in required_dirs:
        dir_path = code_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    # Create __init__.py files to make them packages where appropriate
    packages = ["src", "tests", "models", "scripts", "features", "evaluation", "utils"]
    for pkg_name in packages:
        pkg_path = code_dir / pkg_name / "__init__.py"
        if not pkg_path.exists():
            pkg_path.touch()
            print(f"Created package init: {pkg_path}")
        else:
            print(f"Package init exists: {pkg_path}")

    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
