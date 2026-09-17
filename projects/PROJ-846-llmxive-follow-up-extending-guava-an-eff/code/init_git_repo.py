import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repository(repo_root: Path = None) -> bool:
    """
    Initialize a git repository in the specified directory.
    
    Args:
        repo_root: Path to the repository root. Defaults to current working directory.
        
    Returns:
        True if initialization was successful, False otherwise
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    try:
        # Check if already a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Git repository already initialized at: {repo_root}")
            return True
        
        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=repo_root,
            check=True,
            capture_output=True
        )
        
        print(f"Git repository initialized at: {repo_root}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to initialize git repository: {e}")
        return False
    except FileNotFoundError:
        print("ERROR: Git is not installed or not in PATH")
        return False

def main():
    """Main entry point for git initialization."""
    repo_root = Path.cwd()
    if initialize_git_repository(repo_root):
        print("Git initialization complete.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()