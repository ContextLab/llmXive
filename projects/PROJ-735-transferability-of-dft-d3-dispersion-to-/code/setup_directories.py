"""
Setup script to create required project directories.
Implements T001a: Create directories data/raw/ and data/derived/.
Also implements T001b: Create directories code/ and tests/ if missing.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    root = Path(".")
    
    directories = [
        root / "data" / "raw",
        root / "data" / "derived",
        root / "code",
        root / "tests",
        root / "figures",
        root / "specs",
        root / "docs",
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")

    # Create __init__.py files to ensure they are recognized as packages
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "data" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
          init_file.touch()
          print(f"Created empty __init__.py at: {init_file}")
        else:
          print(f"__init__.py already exists: {init_file}")

if __name__ == "__main__":
    main()