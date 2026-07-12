import os
import sys
from pathlib import Path

def create_directories():
    """
    Initialize the project directory structure required for the pipeline.
    Creates:
      - code/ (if not exists)
      - data/raw/
      - data/processed/
      - data/interim/
      - tests/
      - specs/
    """
    base_path = Path(__file__).parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests",
        "specs"
    ]
    
    created = []
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        else:
            # Ensure subdirectories exist even if parent exists
            if "data" in dir_name and "/" in dir_name:
                # This handles cases like data/raw where parent might exist but subdir doesn't
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created.append(str(dir_path))
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    
    return created

def main():
    """Entry point for project initialization."""
    print("Initializing project structure for PROJ-454...")
    create_directories()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()