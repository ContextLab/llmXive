"""
Setup script to create the project directory structure for T001.
This script ensures all required directories and __init__.py files exist.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    
    # Define the directory structure relative to the code root
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

    for dir_path in dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files
    init_files = [
        project_root / "src" / "__init__.py",
        project_root / "tests" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
          init_file.write_text('"""\nAuto-generated init file.\n"""\n')
          print(f"Created init file: {init_file}")
        else:
          print(f"Init file already exists: {init_file}")

    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
