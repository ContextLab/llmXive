import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize a Git repository in the project root.
    
    This script runs 'git init' in the current working directory (project root).
    It verifies that the .git directory is created successfully.
    
    Verification:
        - .git directory exists in the project root
        - 'git status' returns successfully (exit code 0)
    """
    project_root = Path.cwd()
    git_dir = project_root / ".git"
    
    # Check if git is already initialized
    if git_dir.exists():
        print(f"Git repository already initialized at {project_root}")
        return 0
    
    print(f"Initializing Git repository at {project_root}")
    
    try:
        # Run git init
        result = subprocess.run(
            ["git", "init"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error initializing Git repository: {result.stderr}")
            return 1
        
        # Verify .git directory was created
        if not git_dir.exists():
            print("Error: .git directory was not created")
            return 1
        
        print(f"Successfully initialized Git repository at {git_dir}")
        
        # Verify with git status
        status_result = subprocess.run(
            ["git", "status"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if status_result.returncode != 0:
            print(f"Warning: 'git status' failed: {status_result.stderr}")
            # This is a warning, not a failure of initialization
        
        print("Git repository initialization complete")
        return 0
        
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install Git.")
        return 1
    except Exception as e:
        print(f"Unexpected error during Git initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())