"""
Script to initialize the llmXive project directory structure.
This script creates all necessary directories and __init__.py files
as specified in task T001.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define all required directories relative to the project root
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/models",
        "docs/reports",
        "src/lib",
        "src/services",
        "src/cli",
        "src/config",
        "src/models",
    ]

    created_count = 0
    init_count = 0

    for dir_path in directories:
        full_path = root / dir_path
        
        # Create directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        
        # Create __init__.py file if it doesn't exist
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""{dir_path} package."""\n')
            init_count += 1
            print(f"Created __init__.py: {dir_path}/__init__.py")

    print(f"\nSetup complete: {created_count} directories created, {init_count} __init__.py files created.")

if __name__ == "__main__":
    main()