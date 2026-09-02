import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure.
    Directories: code/, data/raw/, data/processed/, data/analysis/,
                 models/, analysis/, tests/, docs/
    """
    base_dir = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/analysis",
        "models",
        "analysis",
        "tests",
        "docs"
    ]
    
    created_count = 0
    for dir_name in directories:
        target_path = base_dir / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")
    
    return created_count

def main():
    """Main entry point for project setup."""
    print("Starting project directory creation...")
    count = create_directories()
    print(f"Project setup complete. Created {count} new directories.")

if __name__ == "__main__":
    main()