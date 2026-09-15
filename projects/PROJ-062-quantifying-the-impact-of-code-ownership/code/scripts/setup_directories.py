import os
from pathlib import Path

def create_directories():
    """
    Create the required data directory structure:
    - data/raw/
    - data/intermediate/
    - data/results/
    
    Each directory will contain a .gitkeep file to ensure they are tracked by git.
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
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created directory: {directory} with .gitkeep")
        else:
            print(f"Directory already exists: {directory}")
    
    print("Data directory structure setup complete.")

def main():
    create_directories()

if __name__ == "__main__":
    main()