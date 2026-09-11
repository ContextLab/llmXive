"""
Script to initialize a Git repository in the src/ directory.
This must be executed before any other git operations.
"""
import os
import subprocess
import sys
from pathlib import Path


def initialize_git_repository(root_dir: Path) -> bool:
    """
    Initialize a git repository in the specified directory.

    Args:
        root_dir: Path to the directory where git should be initialized.

    Returns:
        True if successful, False otherwise.
    """
    src_dir = root_dir / "src"
    
    if not src_dir.exists():
        print(f"Error: Directory '{src_dir}' does not exist. Cannot initialize git.")
        return False

    try:
        # Change to the src directory
        os.chdir(src_dir)
        
        # Check if git is already initialized
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Git repository already initialized in '{src_dir}'")
            return True
        
        # Initialize the repository
        print(f"Initializing Git repository in '{src_dir}'...")
        init_result = subprocess.run(
            ["git", "init"],
            capture_output=True,
            text=True
        )
        
        if init_result.returncode != 0:
            print(f"Error initializing git: {init_result.stderr}")
            return False
        
        print("Git repository initialized successfully.")
        
        # Configure default user if not set (optional but helpful)
        subprocess.run(["git", "config", "user.name", "llmXive"], capture_output=True)
        subprocess.run(["git", "config", "user.email", "llmXive@example.com"], capture_output=True)
        
        return True

    except FileNotFoundError:
        print("Error: 'git' command not found. Please install Git.")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    """Main entry point for the script."""
    # Determine the project root (assuming script is in code/scripts/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Project root: {project_root}")
    
    success = initialize_git_repository(project_root)
    
    if not success:
        sys.exit(1)
    else:
        print("Task T005c completed: Git repository initialized in src/")


if __name__ == "__main__":
    main()
