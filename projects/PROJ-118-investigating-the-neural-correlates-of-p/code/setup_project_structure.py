import os
from pathlib import Path

def setup_directories():
    """
    Creates the required project directory structure for PROJ-118.
    Ensures the following directories exist under the project root:
    - data/raw
    - data/processed
    - code
    - tests
    - results
    
    Also creates .gitkeep files in data directories to ensure they are tracked by git.
    """
    # Determine project root based on the task description
    # The task specifies the project is at: projects/PROJ-118-investigating-the-neural-correlates-of-p/
    # We assume the script is run from the repository root or the project root.
    # To be safe, we look for the specific project directory name.
    
    current_dir = Path.cwd()
    project_root = None
    
    # Check if we are already in the project root
    if current_dir.name == "PROJ-118-investigating-the-neural-correlates-of-p":
        project_root = current_dir
    else:
        # Look for the project directory in the parent or current path
        # If running from repo root, the project is in projects/...
        possible_root = current_dir / "projects" / "PROJ-118-investigating-the-neural-correlates-of-p"
        if possible_root.exists() and possible_root.is_dir():
            project_root = possible_root
        else:
            # Fallback: assume current dir is the project root if the structure matches
            # This handles cases where the script is moved or run differently
            project_root = current_dir

    # Define relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]

    created_count = 0
    
    for dir_name in directories:
        full_path = project_root / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Directory created/exists: {full_path}")
            created_count += 1
            
            # Add .gitkeep to data directories to ensure they are tracked
            if "data" in dir_name:
                gitkeep_path = full_path / ".gitkeep"
                if not gitkeep_path.exists():
                    gitkeep_path.touch()
                    print(f"  -> Created .gitkeep in {full_path}")
                    
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            raise

    print(f"Project structure setup complete. Created/Verified {created_count} directories.")
    return project_root

def main():
    """Entry point for the script."""
    print("Starting project structure setup for PROJ-118...")
    root = setup_directories()
    print(f"Project root identified at: {root}")

if __name__ == "__main__":
    main()
