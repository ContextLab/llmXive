import os
from pathlib import Path

def create_directories():
    """
    Create the src/ directory and its required subdirectories:
    data/, analysis/, viz/, utils/.
    Also creates a .gitkeep file in src/ to ensure the directory is tracked by git.
    """
    root = Path.cwd()
    src_dir = root / "src"
    
    subdirs = ["data", "analysis", "viz", "utils"]
    
    # Create the main src directory
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    for subdir in subdirs:
        (src_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep in src/ to ensure it is tracked by git
    gitkeep_path = src_dir / ".gitkeep"
    gitkeep_path.touch()
    
    # Verification
    if not src_dir.exists():
        raise FileNotFoundError(f"Failed to create {src_dir}")
    
    for subdir in subdirs:
        subdir_path = src_dir / subdir
        if not subdir_path.exists():
            raise FileNotFoundError(f"Failed to create {subdir_path}")
    
    if not gitkeep_path.exists():
        raise FileNotFoundError(f"Failed to create {gitkeep_path}")
    
    print(f"Successfully created {src_dir} with subdirectories: {subdirs}")
    print(f"Created {gitkeep_path} for git tracking.")
    return True

def main():
    try:
        create_directories()
    except Exception as e:
        print(f"Error creating directories: {e}")
        raise

if __name__ == "__main__":
    main()