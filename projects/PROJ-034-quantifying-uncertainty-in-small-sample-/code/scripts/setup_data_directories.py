import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required data directory structure for the project.
    
    Creates:
    - data/raw/
    - data/simulated/
    - data/results/
    
    Each directory will contain a .gitkeep file to ensure the directory
    is tracked by git even when empty.
    """
    # Define the project root (assuming this script is in code/scripts/)
    # We need to go up two levels to reach the project root
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "simulated",
        project_root / "data" / "results"
    ]
    
    created_dirs = []
    
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_dirs.append(dir_path)
        else:
            print(f"Directory already exists: {dir_path}")
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {dir_path}")
    
    return created_dirs

def main():
    """Main entry point for the script."""
    print("Setting up data directories...")
    created = create_directories()
    print(f"Setup complete. Created/verified {len(created)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())