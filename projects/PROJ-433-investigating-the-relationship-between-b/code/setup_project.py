import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure as per the implementation plan.
    Creates: data/raw, data/processed, data/results, code/, tests/, state/
    """
    root = Path(__file__).resolve().parent.parent
    
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "code",
        root / "tests",
        root / "state",
    ]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
