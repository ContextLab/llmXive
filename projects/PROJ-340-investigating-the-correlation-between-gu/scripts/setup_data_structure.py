"""
Script to initialize the data directory structure for the project.
This script creates the necessary directories under data/ as defined in T001c.
"""
import os
from pathlib import Path

def main():
    base_dir = Path("data")
    
    # Define the required subdirectories
    directories = [
        "raw",
        "processed",
        "results",
        "config",
        "metadata",
        "citations"
    ]
    
    # Create directories
    for dir_name in directories:
        dir_path = base_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files in each directory to ensure they are treated as packages
    init_file = base_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Data directory initialization\n")
        print(f"Created: {init_file}")
    
    # Create __init__.py for subdirectories if they don't exist
    for dir_name in directories:
        dir_path = base_dir / dir_name
        init_path = dir_path / "__init__.py"
        if not init_path.exists():
            init_path.write_text(f"# {dir_name} data directory\n")
            print(f"Created: {init_path}")

    print("Data directory structure initialization complete.")

if __name__ == "__main__":
    main()