"""
Script to initialize the project directory structure.
Creates directories for source code, tests, raw/processed data, and results.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    
    # Define directory structure relative to project root
    dirs = [
        root / "code",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "results",
        root / "figures",
        root / "code" / "utils",
        root / "code" / "data",
        root / "code" / "features",
        root / "code" / "models",
        root / "code" / "eval",
        root / "code" / "interpret",
        root / "code" / "report",
        root / "code" / "pipeline",
        root / "tests" / "unit",
        root / "tests" / "integration",
    ]

    created_count = 0
    for dir_path in dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(root)}")

    print(f"\nProject structure initialized. Created {created_count} new directories.")

    # Create placeholder __init__.py files to ensure Python package recognition
    # and to prevent import errors later.
    init_files = [
        root / "code" / "__init__.py",
        root / "code" / "utils" / "__init__.py",
        root / "code" / "data" / "__init__.py",
        root / "code" / "features" / "__init__.py",
        root / "code" / "models" / "__init__.py",
        root / "code" / "eval" / "__init__.py",
        root / "code" / "interpret" / "__init__.py",
        root / "code" / "report" / "__init__.py",
        root / "code" / "pipeline" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "tests" / "unit" / "__init__.py",
        root / "tests" / "integration" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file.relative_to(root)}")

if __name__ == "__main__":
    main()