"""
Script to create the required project directory structure and placeholder files.
This satisfies T001 by programmatically ensuring the tree exists.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to this script's location or current dir
    # The task specifies paths relative to the project root.
    # We assume this script runs from the project root or we resolve relative to itself.
    base_dir = Path(__file__).parent / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"

    # Directories to create
    dirs = [
        "src",
        "src/data",
        "src/train",
        "src/eval",
        "src/analyze",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
    ]

    created_dirs = []
    for d in dirs:
        full_path = base_dir / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")

    # Files to create (if they don't exist)
    files = [
        "requirements.txt",
        "src/__init__.py",
        "tests/__init__.py",
        "src/data/__init__.py",
        "src/train/__init__.py",
        "src/eval/__init__.py",
        "src/analyze/__init__.py",
        "src/utils/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
    ]

    created_files = []
    for f in files:
        full_path = base_dir / f
        if not full_path.exists():
            # Create empty or minimal content
            full_path.touch()
            created_files.append(str(full_path))
            print(f"Created file: {full_path}")
        else:
            print(f"File exists: {full_path}")

    print("\n--- Setup Summary ---")
    print(f"Created {len(created_dirs)} directories.")
    print(f"Created {len(created_files)} files.")
    print("Project structure T001 verification complete.")

    return 0

if __name__ == "__main__":
    sys.exit(main())