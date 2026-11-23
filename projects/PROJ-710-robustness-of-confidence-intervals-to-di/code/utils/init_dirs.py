"""
Directory Initialization Utilities.
Creates required project directories atomically.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

def create_directories() -> List[Path]:
    """
    Creates all required project directories.
    """
    project_root = Path(__file__).parent.parent
    dirs = [
        project_root / "code",
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "code" / "tests",
        project_root / "artifacts",
        project_root / "figures"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return dirs

def verify_directories() -> bool:
    """
    Verifies that all required directories exist.
    """
    dirs = create_directories()
    for d in dirs:
        if not d.exists():
            return False
    return True

def main():
    """Main entry point."""
    print("Creating directories...")
    dirs = create_directories()
    if verify_directories():
        print("All directories created successfully.")
    else:
        print("Failed to create some directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()