import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure as per the implementation plan.
    Directories created:
      - code
      - code/utils
      - data/raw
      - data/processed
      - tests/unit
      - tests/integration
      - docs/figures
      - state
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs/figures",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_dir / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

def main():
    """
    Entry point for the project structure setup script.
    """
    try:
        create_directories()
        print("Success: Project structure initialized.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during project structure setup: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()