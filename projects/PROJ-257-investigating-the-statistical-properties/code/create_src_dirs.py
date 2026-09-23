import os
from pathlib import Path

def create_directories():
    """Create the source code directories."""
    src_dirs = [
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils"
    ]
    
    for dir_path in src_dirs:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep_path = full_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        
    print(f"Created {len(src_dirs)} source directories with .gitkeep files.")

def main():
    create_directories()
    print("Source directory initialization complete.")

if __name__ == "__main__":
    main()
