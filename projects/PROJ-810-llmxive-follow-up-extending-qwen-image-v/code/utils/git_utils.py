import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def check_git_initialized(project_root: Path) -> Tuple[bool, str]:
    """
    Check if the directory at project_root is a git repository.
    
    Returns:
        Tuple[bool, str]: (is_initialized, message)
    """
    git_dir = project_root / ".git"
    if git_dir.exists() and git_dir.is_dir():
        return True, "Git repository already initialized."
    
    # Check if inside a git repo (could be nested)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip() == "true":
            return True, "Git repository detected (nested or current directory)."
    except FileNotFoundError:
        return False, "Git command not found. Please install Git."
    except Exception as e:
        return False, f"Error checking git status: {str(e)}"
        
    return False, "Git repository not initialized."


def initialize_git_repository(project_root: Path) -> Tuple[bool, str]:
    """
    Initialize a git repository in the specified directory if not already initialized.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    is_init, msg = check_git_initialized(project_root)
    if is_init:
        return True, msg
        
    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        return True, "Git repository initialized successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to initialize git repository: {e.stderr}"
    except FileNotFoundError:
        return False, "Git command not found. Please install Git."
    except Exception as e:
        return False, f"Unexpected error during git initialization: {str(e)}"


def main() -> int:
    """
    Main entry point for git initialization script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Default to current directory if no argument provided
    project_root = Path.cwd()
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        
    if not project_root.exists():
        print(f"Error: Directory '{project_root}' does not exist.")
        return 1
        
    success, message = initialize_git_repository(project_root)
    print(message)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
