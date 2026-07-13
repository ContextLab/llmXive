import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    
    Creates:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    base_dir = Path(__file__).parent
    
    # Define all required directories
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        except OSError as e:
            print(f"Error creating {full_path}: {e}", file=sys.stderr)
            return False
    
    print(f"Successfully created {created_count} directories.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
