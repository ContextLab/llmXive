"""
Scaffold utility for llmXive project.
Generates the core directory structure required for the project.
"""
import os
import sys
from pathlib import Path


def verify_project_root(root_path: Path) -> bool:
    """
    Verify that the provided path is a valid project root.
    
    For this task, we consider a directory a valid project root if it exists
    and is a directory. We do not enforce specific marker files (like .git or 
    pyproject.toml) as they may not exist in all environments.
    
    Args:
        root_path: Path to verify
        
    Returns:
        True if valid, False otherwise
    """
    if not root_path.exists():
        print(f"Error: Project root does not exist: {root_path}", file=sys.stderr)
        return False
    if not root_path.is_dir():
        print(f"Error: Project root is not a directory: {root_path}", file=sys.stderr)
        return False
    return True


def create_directories(root_path: Path, directories: list[str]) -> None:
    """
    Create a list of directories relative to the root path.
    
    Args:
        root_path: The project root directory
        directories: List of relative directory paths to create
    """
    for dir_name in directories:
        full_path = root_path / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")


def main() -> int:
    """
    Main entry point for the scaffold script.
    
    Detects the project root (assumes script is run from project root or 
    detects it relative to the script location) and creates the required
    directory structure.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine project root
    # Strategy 1: Use current working directory if it looks like the project root
    cwd = Path.cwd()
    
    # Strategy 2: If cwd doesn't look like the project root, try to infer from script location
    script_dir = Path(__file__).resolve().parent
    # The script is at code/utils/scaffold.py, so project root is 3 levels up
    inferred_root = script_dir.parent.parent.parent
    
    # Use inferred root if cwd doesn't contain the expected structure or if explicitly in the project
    project_root = inferred_root
    
    # Verify the project root exists
    if not verify_project_root(project_root):
        return 1
    
    print(f"Project root detected: {project_root}")
    
    # Define the core directory structure
    core_directories = [
        "code",
        "data",
        "contracts",
        os.path.join("data", "results"),
        "docs",
        "state",
        "tests",
        "src",
    ]
    
    # Create the directories
    create_directories(project_root, core_directories)
    
    print("Scaffold generation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
