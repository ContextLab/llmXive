"""
Project structure initialization script.
Creates the required directory hierarchy for the llmXive science pipeline.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Creates the standard project directory structure:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    
    Ensures all directories exist, creating them if necessary.
    """
    root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    directories = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "tests",
    ]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(root)))
        else:
            # Ensure directory is writable/accessible
            if not directory.is_dir():
                raise RuntimeError(f"Path {directory} exists but is not a directory.")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    
    return [str(d.relative_to(root)) for d in directories]

def main():
    """Entry point for CLI execution."""
    print("Initializing project structure...")
    dirs = create_project_structure()
    print(f"Project structure ready. Directories: {dirs}")

if __name__ == "__main__":
    main()