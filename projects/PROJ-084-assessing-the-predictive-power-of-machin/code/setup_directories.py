"""
Script to create the required project directory structure.
Implements task T001a: Create code/, data/raw/, data/processed/, data/results/, tests/ directories.
"""
import os
from pathlib import Path

def main():
    """Create the required directories if they do not exist."""
    root = Path(__file__).resolve().parent.parent
    
    directories = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests",
    ]

    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Verify creation by listing
    print("\nVerifying directory structure:")
    for dir_path in directories:
        if dir_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path} does not exist")
            raise FileNotFoundError(f"Failed to create directory: {dir_path}")

    print("\nDirectory structure setup complete.")

if __name__ == "__main__":
    main()
