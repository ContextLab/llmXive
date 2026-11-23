import os
import sys
from pathlib import Path

def create_src_directory(project_root: Path) -> bool:
    """
    Creates the 'src' directory within the project's code root.
    
    Args:
        project_root: The Path to the project root directory 
                      (e.g., projects/PROJ-582-socratic-transformers-dialogue-based-sel/code)
    
    Returns:
        bool: True if the directory was created or already exists, False otherwise.
    """
    src_dir = project_root / "src"
    try:
        src_dir.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {src_dir}: {e}", file=sys.stderr)
        return False

def main():
    # Determine the project root relative to this script's location or current working directory
    # Based on task description, the project root is: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code
    # We assume the script is run from the repository root or the project root context is provided.
    # To be robust, we look for the specific project path relative to cwd.
    
    cwd = Path.cwd()
    target_path = cwd / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    if not target_path.exists():
        print(f"Error: Project code root not found at {target_path}. "
              f"Please ensure you are running this from the repository root.", file=sys.stderr)
        sys.exit(1)
    
    if create_src_directory(target_path):
        print(f"Successfully created or verified directory: {target_path / 'src'}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()