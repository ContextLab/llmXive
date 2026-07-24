"""
Script to initialize the project directory structure for llmXive.
Creates all required directories as per T001a specification.
"""
import os
import sys
from pathlib import Path
from typing import List

def ensure_directories() -> List[str]:
    """
    Creates the required directory structure for the project.
    Returns a list of created directory paths.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/curated",
        "data/results",
        "tests/unit",
        "tests/contract",
        "contracts",
        "docs",
        "paper"
    ]
    
    created = []
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        elif not dir_path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
        
    return created

def main() -> int:
    """Entry point for the project structure setup."""
    print("Initializing llmXive project structure...")
    try:
        created_dirs = ensure_directories()
        print("Successfully created directories:")
        for d in created_dirs:
            print(f"  - {d}")
        
        if not created_dirs:
            print("All directories already exist.")
        
        print("Project structure initialization complete.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
