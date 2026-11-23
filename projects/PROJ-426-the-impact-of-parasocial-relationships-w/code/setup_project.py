import os
import sys
from pathlib import Path

def main():
    """
    Create the project root directory structure for llmXive.
    Implements Task T001a.
    """
    # Define the project root (assuming this script is in code/ or project root)
    # We will create directories relative to the script's parent or current working directory
    # To be safe, we assume the script is run from the project root or code directory.
    # We will enforce creating the structure relative to the current working directory.
    
    root = Path.cwd()
    
    required_dirs = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "contracts",
        "config"
    ]
    
    created = []
    skipped = []
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                created.append(str(full_path))
            else:
                skipped.append(f"Could not create {dir_path} (exists as file)")
        except PermissionError:
            print(f"Permission denied creating: {full_path}")
        except Exception as e:
            print(f"Error creating {dir_path}: {e}")
    
    if created:
        print("Successfully created directories:")
        for d in created:
            print(f"  - {d}")
    else:
        print("No new directories were created.")
        
    if skipped:
        print("Skipped or failed:")
        for s in skipped:
            print(f"  - {s}")

if __name__ == "__main__":
    main()