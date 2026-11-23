"""
Script to create the project directory structure as defined in plan.md.
This ensures the required directories exist before code execution.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/derived",
        "artifacts",
        "tests",
        "specs",
    ]

    created = []
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            # Ensure it's a directory, not a file
            if not path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {path}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")

    # Create .gitkeep files to ensure directories are tracked by git
    for d in dirs:
        path = root / d / ".gitkeep"
        if not path.exists():
            path.touch()
            print(f"Created placeholder: {path}")

if __name__ == "__main__":
    main()