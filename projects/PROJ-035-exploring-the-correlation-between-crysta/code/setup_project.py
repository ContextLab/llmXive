"""
Project structure setup script for PROJ-035-exploring-the-correlation-between-crysta.

Creates the required directory tree:
- src/
- tests/
- data/raw/
- data/cleaned/
- data/results/
- figures/
- contracts/

Run with: python code/setup_project.py
"""
import os
import sys
from pathlib import Path


def setup_project_structure():
    """Create all required project directories and placeholder files."""
    project_root = Path(__file__).parent.parent
    
    # Define directories to create
    directories = [
        "src",
        "src/ingest",
        "src/cleaning",
        "src/descriptors",
        "src/analysis",
        "src/utils",
        "src/config",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "data/raw",
        "data/cleaned",
        "data/results",
        "figures",
        "contracts",
    ]
    
    # Create directories
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files to make directories proper Python packages
    package_init_files = [
        ("src/__init__.py", ""),
        ("src/ingest/__init__.py", ""),
        ("src/cleaning/__init__.py", ""),
        ("src/descriptors/__init__.py", ""),
        ("src/analysis/__init__.py", ""),
        ("src/utils/__init__.py", ""),
        ("src/config/__init__.py", ""),
        ("tests/__init__.py", ""),
        ("tests/unit/__init__.py", ""),
        ("tests/contract/__init__.py", ""),
        ("tests/integration/__init__.py", ""),
    ]
    
    for file_path, content in package_init_files:
        full_path = project_root / file_path
        if not full_path.exists():
            full_path.write_text(content)
            print(f"Created: {file_path}")
        else:
            print(f"File already exists: {file_path}")
    
    # Create .gitkeep files for data directories to ensure they persist in git
    data_keep_files = [
        "data/raw/.gitkeep",
        "data/cleaned/.gitkeep",
        "data/results/.gitkeep",
        "figures/.gitkeep",
        "contracts/.gitkeep",
    ]
    
    for file_path in data_keep_files:
        full_path = project_root / file_path
        if not full_path.exists():
            full_path.write_text("# Keep directory in version control\n")
            print(f"Created: {file_path}")
        else:
            print(f"File already exists: {file_path}")
    
    # Print summary
    print(f"\n=== Project Structure Setup Complete ===")
    print(f"Created {len(created_dirs)} new directories")
    print(f"Created {len([f for f, c in package_init_files if not (project_root / f).exists()])} new __init__.py files")
    print(f"Created {len([f for f in data_keep_files if not (project_root / f).exists()])} new .gitkeep files")
    print(f"\nProject root: {project_root}")
    return 0


if __name__ == "__main__":
    sys.exit(setup_project_structure())