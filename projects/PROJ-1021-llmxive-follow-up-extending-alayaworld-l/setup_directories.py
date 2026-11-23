"""
Script to create the required directory structure and empty __init__.py files
for project PROJ-1021-llmxive-follow-up-extending-alayaworld-l.
"""
import os
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l")
    
    # Define directories to create
    directories = [
        "code",
        "data",
        "tests",
        "config",
        "docs"
    ]
    
    # Create directories
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files in code, tests, and config
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "config/__init__.py"
    ]
    
    for init_file in init_files:
        file_path = project_root / init_file
        file_path.touch()
        print(f"Created empty file: {file_path}")
    
    print(f"Directory structure for {project_root} created successfully.")

if __name__ == "__main__":
    main()