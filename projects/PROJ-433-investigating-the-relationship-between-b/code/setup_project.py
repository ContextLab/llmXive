import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure as per T001.
    Executes: mkdir -p data/raw data/processed data/results code/ tests/ state/
    """
    root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests",
        "state"
    ]

    created = []
    skipped = []

    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            skipped.append(str(full_path))

    print(f"Project structure initialized at: {root}")
    print(f"Created directories: {len(created)}")
    for d in created:
        print(f"  - {d}")
    
    if skipped:
        print(f"Skipped existing directories: {len(skipped)}")
        for d in skipped:
            print(f"  - {d}")

    # Verify existence for the task requirement
    all_exist = all((root / d).exists() for d in required_dirs)
    if not all_exist:
        raise RuntimeError("Failed to create all required project directories.")
    
    print("Verification: All required directories exist.")

if __name__ == "__main__":
    main()
