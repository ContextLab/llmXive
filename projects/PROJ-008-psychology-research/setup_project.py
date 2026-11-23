"""
Project Setup Script for PROJ-008-psychology-research.
Creates the full directory structure, __init__.py files, and .gitkeep files.
"""
import os
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory exists: {path}")

def create_init_file(path: Path) -> None:
    """Create an __init__.py file if it does not exist."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Package initialization\n")
        print(f"Created __init__.py: {init_file}")
    else:
        print(f"__init__.py exists: {init_file}")

def create_gitkeep(path: Path) -> None:
    """Create a .gitkeep file if it does not exist."""
    gitkeep_file = path / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.write_text("# This file ensures the directory is tracked by git.\n")
        print(f"Created .gitkeep: {gitkeep_file}")
    else:
        print(f".gitkeep exists: {gitkeep_file}")

def main() -> None:
    """Main function to set up the project structure."""
    base_dir = Path(__file__).parent / "projects" / "PROJ-008-psychology-research"
    
    # Define directory structure
    directories = [
        "code",
        "code/analysis",
        "code/data",
        "code/utils",
        "code/viz",
        "data",
        "data/raw",
        "data/processed",
        "data/interim",
        "docs",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "contracts",
        "scripts",
        ".github/workflows",
    ]

    # Create directories
    for dir_path in directories:
        full_path = base_dir / dir_path
        ensure_dir(full_path)

    # Create __init__.py files in code and tests subdirectories
    code_dirs = [
        "code",
        "code/analysis",
        "code/data",
        "code/utils",
        "code/viz",
    ]
    tests_dirs = [
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for dir_path in code_dirs + tests_dirs:
        full_path = base_dir / dir_path
        create_init_file(full_path)

    # Create .gitkeep in data/raw
    create_gitkeep(base_dir / "data" / "raw")

    print("\nProject structure setup complete.")

if __name__ == "__main__":
    main()