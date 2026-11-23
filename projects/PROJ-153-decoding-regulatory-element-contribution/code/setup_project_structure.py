import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directory structure as defined in plan.md.
    Directories created:
    - code/
    - tests/ (including subdirectories: unit, integration, contract)
    - data/ (including subdirectories: raw, processed, intermediate)
    - results/
    - figures/
    - specs/
    """
    base_path = Path(".")
    
    directories = [
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/intermediate",
        "results",
        "figures",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure initialization complete. {created_count} new directories created.")
    return created_count

def main():
    """Main entry point for the script."""
    try:
        create_directories()
        print("SUCCESS: Project directory structure created successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Failed to create project structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
