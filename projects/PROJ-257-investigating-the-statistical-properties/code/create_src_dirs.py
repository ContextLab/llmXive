import os
from pathlib import Path

def create_directories():
    """
    Creates the src/ directory structure at the repository root with:
    - data/
    - analysis/
    - viz/
    - utils/
    
    Also creates src/.gitkeep to ensure the directory is tracked by git.
    """
    root = Path(".")
    src_dir = root / "src"
    
    # Define required subdirectories
    subdirs = ["data", "analysis", "viz", "utils"]
    
    # Create the main src directory if it doesn't exist
    src_dir.mkdir(exist_ok=True)
    
    # Create subdirectories and .gitkeep files
    for subdir in subdirs:
        subdir_path = src_dir / subdir
        subdir_path.mkdir(exist_ok=True)
        
        # Create .gitkeep in each subdirectory to ensure tracking
        gitkeep_path = subdir_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
    
    # Create .gitkeep in the main src directory
    src_gitkeep = src_dir / ".gitkeep"
    src_gitkeep.touch(exist_ok=True)
    
    return src_dir, subdirs

def main():
    """Entry point for creating src directory structure."""
    print("Creating src/ directory structure...")
    src_dir, subdirs = create_directories()
    
    # Verification output
    print(f"Created directory: {src_dir}")
    print(f"Created subdirectories: {subdirs}")
    
    # Verify .gitkeep exists
    gitkeep_path = src_dir / ".gitkeep"
    if gitkeep_path.exists():
        print(f"Verified: {gitkeep_path} exists")
    else:
        raise FileNotFoundError(f"Failed to create {gitkeep_path}")
    
    # List contents of src/ for verification
    contents = sorted([p.name for p in src_dir.iterdir() if p.is_dir()])
    print(f"Contents of src/: {contents}")
    
    expected = ["analysis", "data", "utils", "viz"]
    if contents == expected:
        print("Verification PASSED: All required subdirectories exist.")
    else:
        raise ValueError(f"Verification FAILED: Expected {expected}, got {contents}")

if __name__ == "__main__":
    main()
