import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project:
    - data/raw/
    - data/intermediate/
    - data/results/
    
    Each directory is created with a .gitkeep file to ensure they are
    tracked by Git even when empty.
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

def main():
    create_directories()
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()