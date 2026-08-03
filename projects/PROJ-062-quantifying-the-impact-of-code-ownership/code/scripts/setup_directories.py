"""
Script to create the required data directory structure for the project.
This implements Task T004: Setup data/raw/, data/intermediate/, data/results/
with .gitkeep files.
"""
import os
from pathlib import Path

def create_directories():
    """
    Creates the directory structure:
    - data/raw/
    - data/intermediate/
    - data/results/
    
    Each directory will contain a .gitkeep file to ensure they are tracked by Git
    even if they are empty.
    """
    base_dir = Path("data")
    directories = [
        base_dir / "raw",
        base_dir / "intermediate",
        base_dir / "results"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep_path = directory / ".gitkeep"
        
        # Create .gitkeep file if it doesn't exist
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created directory: {directory}")
            print(f"Created .gitkeep file: {gitkeep_path}")
        else:
            print(f"Directory already exists: {directory}")
            print(f".gitkeep file already exists: {gitkeep_path}")
    
    print("\nDirectory structure setup complete.")

def main():
    """Entry point for the script."""
    create_directories()

if __name__ == "__main__":
    main()
