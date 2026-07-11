"""
Script to initialize the project directory structure and create required __init__.py files.
This ensures the project tree exists before any other tasks are executed.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define required directories relative to project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "scripts",
        "state"
    ]

    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
        else:
            # Ensure it is a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path {full_path} exists but is not a directory.")

    # Create __init__.py files if they don't exist
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py"
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text('"""\nAuto-generated init file.\n"""\n')
            print(f"Created: {init_file}")
        else:
            print(f"Exists: {init_file}")

    print(f"Project structure initialized. Created directories: {created_dirs}")

if __name__ == "__main__":
    main()