"""
Script to initialize the project directory structure.
This ensures all required folders exist as per plan.md.
"""
import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "contracts",
        "specs",
        "figures"
    ]
    
    created = []
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
        else:
            print(f"Directory exists: {path}")
    
    # Create __init__.py files if they don't exist
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "contracts" / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All directories already exist.")

if __name__ == "__main__":
    main()
