import os
import sys
from pathlib import Path

def create_directory_structure(root_path: str = ".") -> None:
    """
    Creates the required directory structure for the llmXive science pipeline.
    
    Creates:
    - data/ (and subdirectories: raw/, processed/, residualized/)
    - artifacts/ (and subdirectories: models/, figures/)
    - state/
    
    Args:
        root_path: The root directory relative to which folders will be created.
    """
    base = Path(root_path)
    
    # Define all required directories
    directories = [
        base / "data" / "raw",
        base / "data" / "processed",
        base / "data" / "residualized",
        base / "artifacts" / "models" / "lofo_models",
        base / "artifacts" / "figures",
        base / "state",
    ]
    
    # Create directories
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"\nDirectory structure setup complete. Created {created_count} new directories.")

def main():
    """Entry point for the script."""
    # Determine project root (assuming script is in code/ subdirectory)
    # If running from root, use current dir. If running from code/, go up one level.
    current = Path.cwd()
    if current.name == "code":
        root = current.parent
    else:
        root = current
        
    print(f"Setting up directory structure in: {root}")
    create_directory_structure(str(root))

if __name__ == "__main__":
    main()
