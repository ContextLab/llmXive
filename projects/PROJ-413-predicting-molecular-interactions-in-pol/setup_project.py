"""
Script to initialize the project structure for PROJ-413.
This script creates the necessary directory tree and configuration files.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(".")
    
    # Define directories to create
    directories = [
        "data/raw",
        "data/curated",
        "data/processed",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "results",
        "analysis",
        "docs",
        "tests/contract",
        "tests/integration",
        "state",
        "figures"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    
    # Verify key config files exist
    config_files = [".flake8", "pyproject.toml", "code/requirements.txt"]
    for cfg in config_files:
        if (project_root / cfg).exists():
            print(f"Configuration found: {cfg}")
        else:
            print(f"WARNING: Missing configuration: {cfg}")

if __name__ == "__main__":
    main()