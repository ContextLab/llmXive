import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure:
    - code/
    - data/raw
    - data/processed
    - data/interim
    - tests/unit
    - tests/integration
    - figures/
    - specs/
    
    Also creates .gitkeep files in each directory to ensure they are tracked by git.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    print(f"Creating project structure in: {base_dir}")

    # Define directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/unit",
        "tests/integration",
        "figures",
        "specs",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep to ensure directory is tracked in git
            gitkeep = full_path / ".gitkeep"
            gitkeep.touch()
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create empty __init__.py files in Python package directories
    python_packages = [
        "code",
        "code/models",
        "code/data",
        "code/modeling",
        "code/utils",
        "code/scripts",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    for pkg_path in python_packages:
        full_path = base_dir / pkg_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
