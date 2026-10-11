import os
from pathlib import Path

def main():
    """
    Create core project directories and add .gitkeep files to each.
    This ensures that empty directories are tracked by version control.
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/assets",
        "code",
        "artifacts",
        "tests"
    ]
    
    print("Initializing project directory structure...")
    for directory in directories:
        path = Path(directory)
        # Create directory and any necessary parents
        path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file
        gitkeep_file = path / ".gitkeep"
        gitkeep_file.touch()
        print(f"Verified directory and .gitkeep: {gitkeep_file}")

    print("Core directory setup complete.")

if __name__ == "__main__":
    main()