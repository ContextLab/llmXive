import os
import sys
from pathlib import Path

def create_data_directories(project_root: Path) -> None:
    """
    Create the data directory structure required for the project.
    
    Creates:
    - data/
      - raw/
      - processed/
      - interim/
    
    Args:
        project_root: The root path of the project (e.g., projects/PROJ-424-...)
    """
    data_root = project_root / "data"
    
    subdirs = [
        "raw",
        "processed",
        "interim"
    ]
    
    for subdir in subdirs:
        dir_path = data_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Ensure .gitkeep files exist to preserve empty directories in git
    for subdir in subdirs:
        gitkeep_path = data_root / subdir / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {gitkeep_path}")

def main() -> None:
    """
    Entry point for creating data directories.
    """
    # Determine project root (assuming script is in projects/PROJ-424-.../code/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Project root: {project_root}")
    print("Creating data directory structure...")
    
    create_data_directories(project_root)
    
    # Verify creation
    data_root = project_root / "data"
    print("\nVerifying directory structure:")
    for root, dirs, files in os.walk(data_root):
        level = root.replace(str(data_root), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    main()
