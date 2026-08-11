"""
Project Structure Initialization Script for PROJ-012.

Creates the required directory hierarchy and placeholder files
as specified in tasks.md T001.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure and essential placeholder files."""
    root = Path(".")
    
    # Define required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "state",
        "results/figures",
        # Additional standard directories for robustness
        "specs",
        "contracts",
        "docs",
    ]
    
    # Create directories
    created_dirs = []
    for d in directories:
        full_path = root / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create placeholder files (empty or minimal content) to ensure directories are tracked
    # and to satisfy the requirement of "with at least placeholder files"
    placeholders = [
        ("data/raw/.gitkeep", "# Raw data storage - do not commit large files here"),
        ("data/processed/.gitkeep", "# Processed data storage"),
        ("code/.gitkeep", "# Code directory"),
        ("tests/.gitkeep", "# Tests directory"),
        ("state/.gitkeep", "# State and cache files"),
        ("results/figures/.gitkeep", "# Generated figures"),
        ("specs/.gitkeep", "# Specification documents"),
        ("contracts/.gitkeep", "# Schema contracts"),
    ]
    
    created_files = []
    for rel_path, content in placeholders:
        full_path = root / rel_path
        if not full_path.exists():
            full_path.write_text(content + "\n")
            created_files.append(str(full_path))
    
    # Report
    print(f"Project structure initialized for PROJ-012.")
    print(f"Created directories: {len(created_dirs)}")
    for d in created_dirs:
        print(f"  - {d}")
    print(f"Created placeholder files: {len(created_files)}")
    for f in created_files:
        print(f"  - {f}")
    
    return 0

if __name__ == "__main__":
    exit(main())