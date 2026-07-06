"""
Setup script to initialize the project's data directory structure.
Creates the necessary subdirectories under 'data/' and a .gitignore file.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    # Define required subdirectories
    subdirs = ["raw", "processed", "metrics", "atlas"]
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    for subdir in subdirs:
        subdir_path = data_dir / subdir
        subdir_path.mkdir(exist_ok=True)
        print(f"Created directory: {subdir_path}")
    
    # Create .gitignore for large files in data/
    gitignore_path = data_dir / ".gitignore"
    gitignore_content = """# Ignore all large data files
*
# But keep this directory structure and any .gitkeep files
!.gitkeep
"""
    # Only write if file doesn't exist or content differs
    if not gitignore_path.exists() or gitignore_path.read_text() != gitignore_content:
        gitignore_path.write_text(gitignore_content)
        print(f"Created/updated: {gitignore_path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for subdir in subdirs:
        keep_file = data_dir / subdir / ".gitkeep"
        keep_file.write_text("# Keep this directory in git\n")
        print(f"Created .gitkeep: {keep_file}")

if __name__ == "__main__":
    main()