"""
Script to initialize the top-level directory structure and subdirectories
for the llmXive automated science pipeline project.

This script creates:
- code/, data/, tests/, docs/ at the root
- data/raw/, data/processed/, data/interim/
- .gitkeep files in all directories to ensure they are tracked by git.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist and add a .gitkeep file."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text(f"# This directory contains {path.name}.\n")
        print(f"Created directory: {path}")

def main() -> None:
    root = Path(".")
    
    # Top-level directories
    dirs = [
        root / "code",
        root / "data",
        root / "tests",
        root / "docs",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "interim",
    ]
    
    for d in dirs:
        ensure_dir(d)
    
    print("Directory structure initialization complete.")

if __name__ == "__main__":
    main()