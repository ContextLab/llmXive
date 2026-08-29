import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project root directories explicitly:
    code/, data/raw, data/processed, data/results, tests/.
    
    This function ensures the directory structure exists for the pipeline.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "results",
        base_dir / "tests",
    ]
    
    created = []
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(str(directory))
        print(f"Created directory: {directory}")
        
    return created

def main():
    """Main entry point for directory creation."""
    print("Starting directory creation...")
    created_dirs = create_directories()
    print(f"Successfully created {len(created_dirs)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())