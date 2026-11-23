"""
Project Setup Script.
Creates the required directory structure for the llmXive science pipeline.
"""
import os
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in plan.md.
    
    Directories created:
    - code/
    - data/raw/
    - data/intermediate/
    - data/processed/
    - outputs/
    - tests/
    - contracts/
    - .github/workflows/
    """
    base_path = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "outputs",
        "tests",
        "contracts",
        ".github/workflows",
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    return created_count

def main():
    """Entry point for the setup script."""
    create_directories()

if __name__ == "__main__":
    main()