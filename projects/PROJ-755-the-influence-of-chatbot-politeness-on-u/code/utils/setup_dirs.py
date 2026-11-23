"""
Setup script to create the required project directory structure.
Implements Task T001a for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path
from typing import List

def ensure_directories() -> List[str]:
    """
    Creates all required project directories using os.makedirs with exist_ok=True.
    
    Returns:
        List[str]: A list of the directory paths that were created or verified.
    """
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state"
    ]
    
    project_root = Path(__file__).parent.parent.parent
    
    created_or_verified = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            os.makedirs(full_path, exist_ok=True)
            created_or_verified.append(str(full_path))
        except PermissionError as e:
            print(f"Error: Permission denied creating directory {full_path}: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to create directory {full_path}: {e}", file=sys.stderr)
            sys.exit(1)
            
    return created_or_verified

def main():
    """
    Entry point for the script.
    Creates directories and prints a success message.
    """
    print("Starting directory setup for project...")
    directories = ensure_directories()
    
    if not directories:
        print("No directories were created or verified. Check permissions.")
        sys.exit(1)
    
    print(f"Successfully verified/created {len(directories)} directories:")
    for d in directories:
        print(f"  - {d}")
        
    print("Directory setup complete.")

if __name__ == "__main__":
    main()
