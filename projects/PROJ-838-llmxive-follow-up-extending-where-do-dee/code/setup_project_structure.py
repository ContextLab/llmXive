"""
Script to initialize the project directory structure.
This script ensures all required directories exist as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    directories = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/processed",
        "data/processed/graphs",
        "graphs", # Explicitly requested in task description
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_dir / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    # Ensure __init__.py files exist for Python packages
    init_files = [
        base_dir / "code" / "__init__.py",
        base_dir / "tests" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text("# Package initialization\n")
            print(f"Created init file: {init_file}")
        else:
            print(f"Init file exists: {init_file}")

    # Ensure .gitkeep files exist for data directories to track them in git
    gitkeep_files = [
        base_dir / "data" / "raw" / ".gitkeep",
        base_dir / "data" / "processed" / ".gitkeep",
        base_dir / "data" / "processed" / "graphs" / ".gitkeep",
        base_dir / "graphs" / ".gitkeep",
    ]
    
    for gitkeep in gitkeep_files:
        if not gitkeep.exists():
            gitkeep.write_text("# Placeholder to ensure directory is tracked by git\n")
            print(f"Created .gitkeep: {gitkeep}")
        else:
            print(f".gitkeep exists: {gitkeep}")

    print(f"Project structure initialization complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()