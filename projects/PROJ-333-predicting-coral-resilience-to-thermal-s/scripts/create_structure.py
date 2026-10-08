"""
Script to initialize the project directory structure for llmXive Project.
This script creates the required directories as per T001a.
"""
import os
from pathlib import Path

def main():
    # Define the project root (current directory)
    root = Path(".")

    # Define the required directories relative to the root
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "results/plots",
        "specs/001-coral-resilience-prediction",
    ]

    print(f"Creating project structure in: {root.absolute()}")

    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Ensure __init__.py files exist to make them packages
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "data" / "__init__.py",
        root / "results" / "__init__.py",
        root / "specs" / "001-coral-resilience-prediction" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file.relative_to(root)}")
        else:
            print(f"Init file already exists: {init_file.relative_to(root)}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()