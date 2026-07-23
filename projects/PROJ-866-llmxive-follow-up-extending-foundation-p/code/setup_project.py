import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the core project directory structure:
    code/, data/, tests/, state/, contracts/
    
    Also creates subdirectories for data organization:
    data/raw/, data/processed/, data/results/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create
    directories = [
        "code",
        "code/generators",
        "code/engines",
        "code/utils",
        "code/analysis",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "state",
        "state/projects",
        "contracts",
        "figures"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure verification complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for script execution."""
    try:
        create_structure()
        print("Success: Project structure initialized.")
        return 0
    except Exception as e:
        print(f"Error: Failed to create project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())