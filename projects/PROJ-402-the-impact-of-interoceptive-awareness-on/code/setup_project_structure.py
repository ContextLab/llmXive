"""
Setup script to initialize the project directory structure.
This script creates the necessary directories and placeholder files
as defined in T001.
"""
import os
from pathlib import Path

def create_directories():
    """Create the core project directories."""
    base_dir = Path(__file__).parent.parent
    dirs = [
        base_dir / "code",
        base_dir / "tests",
        base_dir / "data",
        base_dir / "data" / "raw",
        base_dir / "data" / "derived",
        base_dir / "results",
        base_dir / "results" / "reports",
        base_dir / "results" / "figures",
        base_dir / "results" / "logs",
        base_dir / "contracts",
        base_dir / "code" / "utils",
        base_dir / "specs",
        base_dir / "state" / "projects",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

def create_init_files():
    """Create __init__.py files to make directories Python packages."""
    base_dir = Path(__file__).parent.parent
    init_paths = [
        base_dir / "code" / "__init__.py",
        base_dir / "tests" / "__init__.py",
        base_dir / "data" / "__init__.py",
        base_dir / "results" / "__init__.py",
        base_dir / "contracts" / "__init__.py",
        base_dir / "code" / "utils" / "__init__.py",
    ]
    for p in init_paths:
        if not p.exists():
          p.write_text('"""Package initialization."""\n')
          print(f"Created __init__.py: {p}")
        else:
          print(f"__init__.py already exists: {p}")

def create_gitkeep_files():
    """Create .gitkeep files to ensure directories are tracked by git."""
    base_dir = Path(__file__).parent.parent
    keep_paths = [
        base_dir / "data" / "raw" / ".gitkeep",
        base_dir / "data" / "derived" / ".gitkeep",
        base_dir / "results" / "reports" / ".gitkeep",
        base_dir / "results" / "figures" / ".gitkeep",
        base_dir / "results" / "logs" / ".gitkeep",
    ]
    for p in keep_paths:
        if not p.exists():
          # Ensure parent dir exists
          p.parent.mkdir(parents=True, exist_ok=True)
          p.write_text("# This directory is tracked by git.\n")
          print(f"Created .gitkeep: {p}")
        else:
          print(f".gitkeep already exists: {p}")

def main():
    """Execute the setup routine."""
    print("Initializing project structure...")
    create_directories()
    create_init_files()
    create_gitkeep_files()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()