import os
from pathlib import Path

def main():
    """
    Creates the project directory structure and initializes __init__.py files
    as specified in T001.
    """
    # Define the root directory (current working directory or project root)
    root = Path(".")

    # List of directories to create
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "code/tests",
        "specs/001-symbolic-memory-edge-robotics/contracts",
        "tests/unit",
        "tests/integration",
    ]

    # List of directories that need an __init__.py file
    init_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "code/tests",
        "specs/001-symbolic-memory-edge-robotics/contracts",
        "tests/unit",
        "tests/integration",
    ]

    created_dirs = []
    created_files = []

    for d in directories:
        dir_path = root / d
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))

    for d in init_dirs:
        dir_path = root / d
        init_file = dir_path / "__init__.py"
        # Create empty __init__.py if it doesn't exist
        if not init_file.exists():
            init_file.touch()
            created_files.append(str(init_file))

    # If this script is run as main, print summary
    if __name__ == "__main__":
        print("Directory structure created:")
        for d in created_dirs:
            print(f"  [DIR] {d}")
        print("Init files created:")
        for f in created_files:
            print(f"  [FILE] {f}")

if __name__ == "__main__":
    main()
