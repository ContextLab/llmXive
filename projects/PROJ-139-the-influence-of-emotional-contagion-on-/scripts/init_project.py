"""
Script to initialize the project directory structure.
Run this once to ensure all required folders exist.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    
    # Define the required directory structure
    directories = [
        "code",
        "code/utils",
        "code/data",
        "code/config",
        "code/contracts",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/figures",
        "state",
        "state/logs",
        "state/checkpoints",
        "docs",
        "scripts",
        "figures"
    ]

    created = []
    for d in directories:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path.relative_to(root)))
            print(f"Created: {path.relative_to(root)}")
        else:
            print(f"Exists:  {path.relative_to(root)}")

    if not created:
        print("All directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created)} directories.")

if __name__ == "__main__":
    main()