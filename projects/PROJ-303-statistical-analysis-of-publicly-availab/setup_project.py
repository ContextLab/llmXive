"""
Script to initialize the project directory structure and configuration files.
This script is idempotent and can be run multiple times safely.
"""
import os
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    base_dirs = [
        "src/data", "src/models", "src/evaluation", "src/visualization",
        "src/pipeline", "src/scripts", "src/cli",
        "tests/unit", "tests/integration", "tests/contract",
        "data/raw", "data/processed",
        "outputs/plots", "outputs/metrics",
        "state"
    ]
    
    for dir_path in base_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_init_files():
    """Create empty __init__.py files in all Python packages."""
    init_dirs = [
        "src", "src/data", "src/models", "src/evaluation", "src/visualization",
        "src/pipeline", "src/scripts", "src/cli",
        "tests", "tests/unit", "tests/integration", "tests/contract",
        "data", "data/raw", "data/processed",
        "outputs", "outputs/plots", "outputs/metrics",
        "state"
    ]
    
    for dir_path in init_dirs:
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
        else:
            print(f"Already exists: {init_file}")

def main():
    print("Initializing project structure...")
    create_directories()
    create_init_files()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()