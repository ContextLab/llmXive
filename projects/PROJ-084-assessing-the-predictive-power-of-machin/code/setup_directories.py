import os
from pathlib import Path

def main():
    """
    Create the standard project directory structure.
    This script ensures that code/, data/raw/, data/processed/, data/results/, and tests/ exist.
    """
    root = Path(".")
    
    dirs_to_create = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests",
    ]

    created_count = 0
    for d in dirs_to_create:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {d}")
            created_count += 1
        else:
            print(f"Directory already exists: {d}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    main()
