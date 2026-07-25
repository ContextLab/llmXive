import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> None:
    """Create the required project directory structure."""
    base_dir = Path(__file__).resolve().parent.parent
    
    directories: List[Path] = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "curated",
        base_dir / "data" / "results",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "contract",
        base_dir / "contracts",
        base_dir / "docs",
        base_dir / "paper",
        base_dir / "code" / "agent",
        base_dir / "code" / "data",
        base_dir / "code" / "metrics",
        base_dir / "code" / "analysis",
        base_dir / "code" / "utils",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory.relative_to(base_dir)}")
        else:
            print(f"Directory exists: {directory.relative_to(base_dir)}")

    print(f"\nTotal directories created: {created_count}")

def main() -> None:
    """Entry point for project structure setup."""
    create_directories()

if __name__ == "__main__":
    main()