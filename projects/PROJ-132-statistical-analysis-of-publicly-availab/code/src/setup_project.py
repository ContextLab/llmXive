import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the bird migration analysis pipeline.
    Directories created:
    - src/data, src/models, src/analysis, src/utils, src/cli
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    base_path = Path(__file__).resolve().parent.parent.parent
    
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "src/utils",
        "src/cli",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure __init__.py exists in Python packages to make them importable
        if dir_name.startswith("src/") or dir_name.startswith("tests/"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    return created_count

def main():
    """Entry point for the script."""
    print("Creating project directory structure...")
    count = create_directories()
    print(f"Successfully created {count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
