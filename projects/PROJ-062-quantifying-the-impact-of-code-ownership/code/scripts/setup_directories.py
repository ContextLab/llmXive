import os
from pathlib import Path

def create_directories():
    """
    Create the required directory structure for the project:
    - data/raw/
    - data/intermediate/
    - data/results/
    
    Creates .gitkeep files in each to ensure they are tracked by Git.
    """
    base_path = Path(__file__).parent.parent.parent / "data"
    
    directories = [
        base_path / "raw",
        base_path / "intermediate",
        base_path / "results"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created directory: {directory}")
            print(f"Created .gitkeep in: {gitkeep}")
        else:
            print(f"Directory already exists: {directory}")
    
    return True

def main():
    """
    Entry point for the script.
    """
    try:
        create_directories()
        print("Directory structure setup complete.")
    except Exception as e:
        print(f"Error setting up directories: {e}")
        raise

if __name__ == "__main__":
    main()
