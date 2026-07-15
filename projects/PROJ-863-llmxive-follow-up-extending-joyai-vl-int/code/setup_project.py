"""
Script to verify and initialize the project structure.
This script ensures all required directories and __init__.py files exist.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    
    # Define required directories
    required_dirs = [
        "src/data_synthesis",
        "src/feature_extraction",
        "src/baseline",
        "src/scheduler",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/features",
        "data/baseline",
        "data/evaluation",
        "models",
        "figures",
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path.relative_to(root)}")

    # Ensure __init__.py files exist for Python packages
    init_files = [
        "src/__init__.py",
        "src/data_synthesis/__init__.py",
        "src/feature_extraction/__init__.py",
        "src/baseline/__init__.py",
        "src/scheduler/__init__.py",
        "src/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]

    for init_path in init_files:
        full_path = root / init_path
        if not full_path.exists():
            full_path.touch()
            print(f"Created init file: {full_path.relative_to(root)}")
        else:
            print(f"Init file exists: {full_path.relative_to(root)}")

    print(f"\nProject structure verification complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()