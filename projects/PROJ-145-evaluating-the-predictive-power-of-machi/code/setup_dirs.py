import os
from pathlib import Path

def main():
    """
    Create the root directory structure for the project.
    This implements T001a and T001b (directory creation and __init__.py generation).
    """
    # Define the project root (current directory context for the script)
    # Assuming this script runs from the project root or we define relative to cwd
    root = Path.cwd()

    # Define all required directories
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests/unit",
        "tests/integration",
        "specs"
    ]

    created_dirs = []
    for dir_path in dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Create __init__.py files to initialize Python packages
    # Targets for T001b
    init_targets = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    for target in init_targets:
        full_path = root / target / "__init__.py"
        if not full_path.exists():
            full_path.touch()
            print(f"Created __init__.py: {full_path}")
        else:
            print(f"__init__.py already exists: {full_path}")

    # Also ensure __init__.py exists in data subfolders if they are treated as packages
    # though usually data is not a package, we ensure the structure is robust
    for data_sub in ["raw", "processed", "models"]:
        full_path = root / "data" / data_sub / "__init__.py"
        if not full_path.exists():
            full_path.touch()
            print(f"Created __init__.py: {full_path}")

    print("\nDirectory structure setup complete.")
    return created_dirs

if __name__ == "__main__":
    main()
