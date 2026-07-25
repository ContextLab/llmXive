import os
import sys
from pathlib import Path

def setup_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    Creates: src/, tests/, data/raw, data/processed, data/splits, results, contracts/, .github/workflows/
    Places .gitkeep files in each directory to ensure they are tracked by git.
    """
    # Define the project root (current directory)
    root = Path(".")
    
    # Define the directory structure relative to the root
    # Note: The task description mentions 'src/', but existing API surface shows code in 'code/' and 'src/'.
    # We will create 'src/' as requested by the task, and 'code/' is likely the root for scripts.
    # Based on task description: "Create project structure per implementation plan: src/, tests/, data/raw..."
    # We will ensure the directories match the task requirement exactly.
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows",
        "data/fallback", # Added based on T043/T013 requirements for fallback data
        "figures",      # Standard location for plots (referenced in constraints)
    ]
    
    created_count = 0
    
    for dir_path in directories:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep to ensure directory is tracked
            keep_file = full_path / ".gitkeep"
            if not keep_file.exists():
                keep_file.touch()
                created_count += 1
                print(f"Created directory: {full_path} (with .gitkeep)")
            else:
                print(f"Directory exists: {full_path}")
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}")
            return False
    
    print(f"Project structure setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
