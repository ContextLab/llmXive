import os
from pathlib import Path

def create_directories():
    """
    Initialize the project directory structure required for the llmXive pipeline.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/features/
    - tests/
    - state/projects/
    """
    # Determine project root (assuming script is run from project root or code/ subdirectory)
    # We assume the current working directory is the project root for this setup script
    project_root = Path.cwd()
    
    # Define relative paths to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/features",
        "tests",
        "state/projects"
    ]
    
    created = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created

def main():
    """Entry point for directory creation."""
    print("Initializing project directory structure...")
    created_dirs = create_directories()
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
    else:
        print("\nNo new directories created (all already exist).")
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
