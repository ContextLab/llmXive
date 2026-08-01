import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
        base_dir / "specs" / "001-investigating-the-correlation-between-gu" / "contracts",
    ]
    
    created = []
    failed = []
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(base_dir)))
        except OSError as e:
            failed.append(f"{str(directory.relative_to(base_dir))}: {e}")
    
    if failed:
        print(f"Failed to create directories: {', '.join(failed)}")
        return False
    
    print(f"Successfully created {len(created)} directories:")
    for d in created:
        print(f"  - {d}")
    
    return True

def main():
    """Entry point for directory creation script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
