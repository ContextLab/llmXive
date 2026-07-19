import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure explicitly.
    
    Creates:
    - code/
    - data/raw
    - data/processed
    - data/results
    - specs/001-investigating-the-correlation-between-gu/contracts/
    
    Returns:
        dict: A summary of created directories and their absolute paths.
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
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return {
        "created": created,
        "total_created": len(created),
        "base_directory": str(base_dir)
    }

if __name__ == "__main__":
    result = create_directories()
    print(f"Directory creation summary: {result}")