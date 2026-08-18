import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in T001.
    This script ensures all required folders exist relative to the project root.
    """
    # Define the project root (assumed to be the directory containing this script or parent of 'code')
    # We will create directories relative to the current working directory to ensure they land in the project root.
    base_path = Path.cwd()

    # Define the required directory hierarchy
    directories = [
        "code/src/generators",
        "code/src/estimators",
        "code/src/metrics",
        "code/src/viz",
        "code/tests/unit",
        "code/tests/integration",
        "data/",
        "results/",
        "contracts/",
        "config/"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py files to make them Python packages where applicable
    # We only need __init__.py in the code/src subfolders and test folders for imports to work cleanly
    python_packages = [
        "code/src/generators",
        "code/src/estimators",
        "code/src/metrics",
        "code/src/viz",
        "code/tests/unit",
        "code/tests/integration"
    ]

    for pkg_path in python_packages:
        full_path = base_path / pkg_path / "__init__.py"
        if not full_path.exists():
            # Create an empty init file or with a simple docstring
            full_path.write_text("# Auto-generated package initializer\n")
            print(f"Created package init: {full_path}")
            created_count += 1

    print(f"\nProject structure setup complete. {created_count} items created/verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())