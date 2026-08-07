"""
Script to initialize the project directory structure for PROJ-054.
This ensures all required folders and placeholder files exist before
running simulation scripts.
"""
import os
from pathlib import Path

def create_structure():
    root = Path(".")
    
    # Define directories relative to root
    dirs = [
        "code",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/synthetic",
        "data/synthetic/trajectories",
        "figures",
        "docs",
        "specs"
    ]

    # Define files to ensure (with empty content or minimal init)
    files = [
        "code/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "data/.gitkeep",
        "data/synthetic/.gitkeep",
        "figures/.gitkeep",
        "docs/.gitkeep",
        "specs/.gitkeep"
    ]

    created_dirs = 0
    created_files = 0

    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {path}")
            created_dirs += 1
        else:
            # Ensure it's a directory
            if not path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {path}")

    for f in files:
        path = root / f
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            print(f"Created file: {path}")
            created_files += 1
        else:
            # Ensure it's a file
            if not path.is_file():
                raise RuntimeError(f"Path exists but is not a file: {path}")

    print(f"\nProject structure initialized.")
    print(f"Directories created/verified: {created_dirs}")
    print(f"Files created/verified: {created_files}")
    print(f"Ready for implementation.")

if __name__ == "__main__":
    create_structure()