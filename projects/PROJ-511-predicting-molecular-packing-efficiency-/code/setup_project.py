"""
Project Setup Module
Creates the required directory structure for the molecular packing efficiency project.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directory structure:
    - code/
    - data/
    - data/raw_cif/
    - models/
    - results/
    - contracts/
    - specs/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_dir = Path(__file__).parent.parent
    
    required_dirs = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
    ]
    
    created_count = 0
    existing_count = 0
    failed_count = 0
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                print(f"Created directory: {dir_path}")
            else:
                existing_count += 1
                print(f"Directory already exists: {dir_path}")
        except OSError as e:
            failed_count += 1
            print(f"Failed to create directory {dir_path}: {e}", file=sys.stderr)
    
    if failed_count > 0:
        print(f"\nWarning: {failed_count} directory(ies) failed to create.", file=sys.stderr)
        return False
        
    print(f"\nSetup complete. Created: {created_count}, Existing: {existing_count}")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
