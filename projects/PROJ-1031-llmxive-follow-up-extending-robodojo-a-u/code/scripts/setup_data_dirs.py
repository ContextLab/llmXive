import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project data.
    Directories created:
      - code/data/raw/
      - code/data/interim/
      - code/data/processed/
      - code/data/final/
    """
    # Determine the base directory relative to this script location
    # The script is at code/scripts/setup_data_dirs.py
    # The project root is code/
    script_dir = Path(__file__).resolve().parent
    code_root = script_dir.parent
    
    data_base = code_root / "data"
    
    directories = [
        data_base / "raw",
        data_base / "interim",
        data_base / "processed",
        data_base / "final"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Data directory setup complete. {created_count} new directories created.")
    
    # Verify creation by listing
    print("\nVerifying data structure:")
    if data_base.exists():
        for item in sorted(data_base.iterdir()):
            print(f"  {item.name}/")
    else:
        print("  ERROR: Base data directory does not exist!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())