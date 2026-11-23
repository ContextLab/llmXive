"""
Script to initialize the project directory structure for PROJ-358.

This script creates the necessary folders for code, data, tests, docs, 
and contracts as defined in the implementation plan.

Usage:
    python code/setup_structure.py
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root based on the task description path
    # The task specifies: projects/PROJ-358-the-influence-of-network-topology-on-neu
    # However, the prompt constraints say "Stay inside the project tree" and 
    # "All artifact paths are relative to the project root".
    # Given the task explicitly asks to create `projects/PROJ-358-...`,
    # we will create that directory relative to the current working directory.
    
    base_dir = Path("projects/PROJ-358-the-influence-of-network-topology-on-neu")
    
    # Define the subdirectories to create
    subdirs = [
        "code/data",
        "code/analysis",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "docs",
        "contracts"
    ]
    
    created_count = 0
    
    print(f"Setting up project structure at: {base_dir}")
    
    for subdir in subdirs:
        target_path = base_dir / subdir
        
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {target_path}")
            created_count += 1
        else:
            print(f"Exists: {target_path}")
    
    # Create __init__.py files to ensure they are treated as packages
    init_paths = [
        base_dir / "code" / "__init__.py",
        base_dir / "code" / "data" / "__init__.py",
        base_dir / "code" / "analysis" / "__init__.py",
        base_dir / "tests" / "__init__.py",
        base_dir / "tests" / "unit" / "__init__.py",
        base_dir / "tests" / "integration" / "__init__.py",
    ]
    
    for init_path in init_paths:
        # Ensure the parent directory exists first (it should from above)
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.touch()
            print(f"Created empty package marker: {init_path}")
            created_count += 1
    
    print(f"\nSetup complete. {created_count} new items created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
