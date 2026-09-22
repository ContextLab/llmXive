"""
Project setup script to create the required directory structure.
"""
import os
from pathlib import Path

def create_directories():
    """Create all required directories for the project."""
    root = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "outputs",
        "tests",
        "contracts",
        ".github/workflows"
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created

def main():
    """Entry point for the setup script."""
    print("Setting up project directory structure...")
    created_dirs = create_directories()
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
    else:
        print("\nAll directories already exist.")

if __name__ == "__main__":
    main()
