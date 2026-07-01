"""
Project Initialization Script.
Creates the required directory structure for the llmXive pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the standard project directory structure:
    - code/
    - data/raw/
    - data/processed/
    - results/
    - logs/
    
    Returns 0 on success, 1 on failure.
    """
    # Define the project root (assuming script is in code/, go up one level)
    # However, per constraints, we assume execution from project root or script handles relative paths.
    # To be safe, we resolve relative to the script's location if needed, 
    # but standard practice is running from root. We will create relative to current working directory.
    
    root = Path.cwd()
    
    # Define required directories relative to root
    dirs_to_create = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "logs"
    ]
    
    created_count = 0
    existing_count = 0
    failed_count = 0
    
    print(f"Initializing project structure at: {root}")
    
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                # Check if it's actually a directory
                if full_path.is_dir():
                    print(f"Directory already exists: {full_path}")
                    existing_count += 1
                else:
                    print(f"ERROR: Path exists but is not a directory: {full_path}")
                    failed_count += 1
        except OSError as e:
            print(f"ERROR: Failed to create directory {full_path}: {e}")
            failed_count += 1
    
    print("-" * 40)
    print(f"Summary: Created={created_count}, Existing={existing_count}, Failed={failed_count}")
    
    if failed_count > 0:
        print("Project initialization failed.")
        return 1
    
    print("Project structure initialized successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
