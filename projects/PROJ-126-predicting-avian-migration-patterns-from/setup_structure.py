"""
Script to initialize the project directory structure.
This script creates the required directories and empty __init__.py files
to ensure the project tree is ready for development.
"""
import os
from pathlib import Path

def main():
    base_dir = Path(__file__).parent
    
    # Define required directories relative to project root
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/outputs"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory exists: {dir_path}")
    
    # Ensure __init__.py files exist in code and tests
    init_files = [
        base_dir / "code" / "__init__.py",
        base_dir / "tests" / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file.relative_to(base_dir)}")
        else:
            print(f"Init file exists: {init_file.relative_to(base_dir)}")

    if created_dirs:
        print(f"\nSuccessfully initialized {len(created_dirs)} directories.")
    else:
        print("\nAll directories already existed.")

if __name__ == "__main__":
    main()