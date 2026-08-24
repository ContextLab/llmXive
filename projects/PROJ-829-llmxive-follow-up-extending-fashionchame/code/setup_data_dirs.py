import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for llmXive.
    Creates the required folders under the 'code/' directory as per T001.
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    
    # Ensure the base code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)
    
    # Define required directories relative to the project root (base_dir)
    # Per T001: create `code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`
    # Since we are running from code/setup_data_dirs.py, we map these to the project structure:
    # - code/ (already exists as base_dir/code)
    # - data/raw/ -> base_dir/data/raw
    # - data/processed/ -> base_dir/data/processed
    # - tests/unit/ -> base_dir/tests/unit
    # - tests/integration/ -> base_dir/tests/integration
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path.relative_to(base_dir)}")
    
    print("Directory structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
