import os
import sys
from pathlib import Path

def setup_project_structure():
    """
    Creates the exact directory tree required for the project:
    src/, tests/, data/raw/, data/cleaned/, data/results/, figures/, contracts/
    """
    base_dir = Path.cwd()

    # Define the required directories relative to the project root
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/cleaned",
        "data/results",
        "figures",
        "contracts",
        # Subdirectories for modularity as implied by the API surface
        "src/ingest",
        "src/cleaning",
        "src/descriptors",
        "src/analysis",
        "src/utils",
        "src/config",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory exists: {dir_path}")

    # Create __init__.py files to ensure packages are recognized
    package_dirs = [
        "src", "tests", "src/ingest", "src/cleaning", "src/descriptors",
        "src/analysis", "src/utils", "src/config", "tests/unit",
        "tests/integration", "tests/contract"
    ]
    for pkg_dir in package_dirs:
        init_file = base_dir / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created package init: {init_file}")

    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_project_structure()
