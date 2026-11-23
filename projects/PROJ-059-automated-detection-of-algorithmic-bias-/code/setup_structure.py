import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    Creates: src/bias_pipeline, src/cli, data/raw, data/processed, data/validation,
             tests/unit, tests/integration, state
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        "src/bias_pipeline",
        "src/cli",
        "data/raw",
        "data/processed",
        "data/validation",
        "tests/unit",
        "tests/integration",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory creation complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()
