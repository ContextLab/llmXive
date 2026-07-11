"""
Script to initialize the project directory structure and empty __init__.py files.
This script is idempotent and safe to run multiple times.
"""
import os
import sys
from pathlib import Path

def ensure_dir(path: Path):
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory exists: {path}")

def ensure_init(path: Path):
    """Create __init__.py if it doesn't exist."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Created __init__.py: {init_file}")
    else:
        print(f"__init__.py exists: {init_file}")

def main():
    base = Path(__file__).parent
    
    # Define directory structure
    dirs = [
        base / "src" / "generators",
        base / "src" / "agents",
        base / "src" / "analysis",
        base / "src" / "utils",
        base / "tests",
        base / "tests" / "contract",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "data",
        base / "data" / "results",
    ]

    # Create directories
    for d in dirs:
        ensure_dir(d)

    # Create __init__.py files
    for d in dirs:
        ensure_init(d)

    # Create .gitkeep files for data directories to ensure they are tracked by git
    data_dirs = [
        base / "data",
        base / "data" / "results",
    ]
    for d in data_dirs:
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep: {gitkeep}")
        else:
            print(f".gitkeep exists: {gitkeep}")

    print("\nDirectory structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())