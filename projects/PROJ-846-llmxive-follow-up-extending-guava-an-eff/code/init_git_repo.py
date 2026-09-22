import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repository(root_path: Path) -> bool:
    """
    Initialize a git repository in the specified root path.
    
    Args:
        root_path: The directory where the git repository should be initialized.
        
    Returns:
        True if initialization was successful, False otherwise.
    """
    if not root_path.exists():
        print(f"Error: Path does not exist: {root_path}")
        return False
        
    try:
        # Change to the root directory
        os.chdir(root_path)
        
        # Run git init
        result = subprocess.run(
            ["git", "init"],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"Git initialized successfully in {root_path}")
        print(f"Output: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error initializing git repository: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: git command not found. Please install git and try again.")
        return False

def main():
    """Main entry point for git initialization."""
    # Determine the project root path
    # The project root is the parent of the 'code' directory
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent.parent.parent.parent.parent.parent.parent
    
    print(f"Initializing git repository in: {project_root}")
    
    if initialize_git_repository(project_root):
        print("Git initialization completed successfully.")
        sys.exit(0)
    else:
        print("Git initialization failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()