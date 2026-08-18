import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in T001.
    Directories: data/raw, data/processed, code, figures, analysis, contracts
    """
    base_dir = Path(".")
    
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "figures",
        "analysis",
        "contracts"
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
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
