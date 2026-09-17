import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required data directory structure:
    - data/raw
    - data/simulated
    - data/results
    
    Each directory will contain a .gitkeep file to ensure they are tracked by git
    even if empty.
    """
    # Define the project root (assuming scripts are in code/scripts/)
    # We need to go up two levels to reach the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "simulated",
        project_root / "data" / "results"
    ]
    
    created_dirs = []
    
    for dir_path in data_dirs:
        # Create the directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
            print(f"Created .gitkeep in: {gitkeep_path}")
        else:
            print(f"Directory already exists: {dir_path}")
            print(f".gitkeep already exists: {gitkeep_path}")
        
        created_dirs.append(str(dir_path))
    
    return created_dirs

def main():
    """
    Main entry point for the script.
    """
    print("Setting up data directories...")
    created = create_directories()
    print(f"\nSetup complete. Created/verified {len(created)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())