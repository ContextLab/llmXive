import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo(project_root: Path) -> bool:
    """
    Initialize a git repository in the given project root if one does not already exist.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if initialization was successful or repo already exists, False otherwise.
    """
    git_dir = project_root / ".git"
    
    if git_dir.exists():
        print(f"Git repository already initialized at {project_root}")
        return True
    
    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Git repository initialized successfully at {project_root}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {e.stderr}")
        return False

def verify_git_repo(project_root: Path) -> bool:
    """
    Verify that a git repository exists and is functional in the project root.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        True if repository is valid, False otherwise.
    """
    git_dir = project_root / ".git"
    
    if not git_dir.exists():
        print("Git repository does not exist.")
        return False
    
    try:
        result = subprocess.run(
            ["git", "status"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print("Git repository verification successful.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git repository verification failed: {e.stderr}")
        return False

def main() -> int:
    """
    Main entry point for the git initialization script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    project_root = Path.cwd()
    print(f"Working directory: {project_root}")
    
    if not initialize_git_repo(project_root):
        return 1
    
    if not verify_git_repo(project_root):
        return 1
    
    print("Git initialization task completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
