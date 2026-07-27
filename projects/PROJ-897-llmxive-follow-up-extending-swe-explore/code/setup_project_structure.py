import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> None:
    """Create the standard project directory structure."""
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
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main() -> None:
    """Entry point for the project structure setup."""
    print("Setting up project directory structure...")
    create_directories()
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
