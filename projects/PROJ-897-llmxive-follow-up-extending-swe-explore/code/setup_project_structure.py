import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> None:
    """Create the project directory structure as defined in tasks.md."""
    root = Path(__file__).resolve().parent.parent
    
    directories: List[Path] = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "curated",
        root / "data" / "results",
        root / "tests" / "unit",
        root / "tests" / "contract",
        root / "contracts",
        root / "docs",
        root / "paper",
        root / "state",
        root / "figures",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory.relative_to(root)}")

def main() -> None:
    """Entry point for the script."""
    print("Setting up project directory structure...")
    create_directories()
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
