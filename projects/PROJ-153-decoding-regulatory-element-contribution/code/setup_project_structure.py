import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directory structure as defined in plan.md.
    Directories created:
      - code/
      - tests/ (including unit, contract, integration subfolders)
      - data/ (including raw, processed, interim subfolders)
      - results/ (including figures, tables subfolders)
    """
    base_dir = Path(__file__).parent.parent
    
    # Define the directory structure relative to the project root
    directories = [
        "code",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/interim",
        "results/figures",
        "results/tables",
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
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the script."""
    try:
        create_directories()
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
