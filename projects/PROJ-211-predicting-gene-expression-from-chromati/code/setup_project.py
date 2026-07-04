import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-211-predicting-gene-expression-from-chromati.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/models/
    - logs/
    - tests/contract/
    - tests/integration/
    - tests/unit/
    - docs/
    - contracts/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "logs",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
        "contracts"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1
    
    print(f"\nProject structure setup complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped: {skipped_count} directories (already exist)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
