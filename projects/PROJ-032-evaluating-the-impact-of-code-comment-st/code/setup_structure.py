import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as specified in T001.
    This script ensures the following directories exist:
    - src/code
    - src/data/raw
    - src/data/processed
    - src/data/schemas
    - tests/unit
    - tests/integration
    - docs
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "src" / "code",
        base_dir / "src" / "data" / "raw",
        base_dir / "src" / "data" / "processed",
        base_dir / "src" / "data" / "schemas",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        base_dir / "docs"
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"Directory exists: {directory.relative_to(base_dir)}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already exist.")

    return 0

if __name__ == "__main__":
    sys.exit(main())