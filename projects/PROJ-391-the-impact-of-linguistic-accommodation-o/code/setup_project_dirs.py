"""
Script to create the required project directory structure for PROJ-391.
Implements Task T001a.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "outputs",
        "outputs/figures",
        "outputs/reports"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
