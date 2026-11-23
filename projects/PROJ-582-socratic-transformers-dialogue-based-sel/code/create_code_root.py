"""
Task T001a: Create project code root.

Creates the directory:
projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/
"""
import os
import sys
from pathlib import Path

def create_code_root(project_root: str = "projects/PROJ-582-socratic-transformers-dialogue-based-sel") -> Path:
    """
    Creates the 'code' directory inside the specified project root.

    Args:
        project_root: Relative path to the project root directory.

    Returns:
        Path object pointing to the created 'code' directory.

    Raises:
        OSError: If the directory cannot be created.
    """
    code_dir = Path(project_root) / "code"
    
    # Ensure the parent project root exists first
    if not code_dir.parent.exists():
        code_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the code directory
    code_dir.mkdir(parents=True, exist_ok=True)
    
    return code_dir

def main():
    """
    Main entry point for T001a.
    Creates the directory and verifies its existence.
    """
    project_root = "projects/PROJ-582-socratic-transformers-dialogue-based-sel"
    code_dir = create_code_root(project_root)
    
    # Verification as per task description
    assert os.path.isdir(str(code_dir)), f"Failed to create directory: {code_dir}"
    assert code_dir.is_dir(), f"Path is not a directory: {code_dir}"
    
    print(f"Successfully created code root: {code_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())