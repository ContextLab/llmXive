import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo(root_dir: Path) -> bool:
    """
    Initialize a git repository in the specified directory if one does not already exist.
    Returns True if successful, False otherwise.
    """
    if not root_dir.exists():
        print(f"Error: Directory {root_dir} does not exist.")
        return False

    git_dir = root_dir / ".git"
    if git_dir.exists():
        print(f"Git repository already initialized in {root_dir}.")
        return True

    try:
        subprocess.run(["git", "init"], cwd=root_dir, check=True, capture_output=True, text=True)
        print(f"Git repository initialized in {root_dir}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {e.stderr}")
        return False

def configure_git_ignore(root_dir: Path, gitignore_path: Path) -> bool:
    """
    Move or copy the .gitignore file to the root of the repository if it's not already there.
    Ensures the .gitignore file exists at the root level.
    """
    target_gitignore = root_dir / ".gitignore"
    
    if target_gitignore.exists():
        print(f".gitignore already exists at {target_gitignore}.")
        return True

    if not gitignore_path.exists():
        print(f"Error: Source .gitignore file not found at {gitignore_path}.")
        return False

    try:
        # Copy the content to ensure it's in the right place
        with open(gitignore_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(target_gitignore, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        print(f".gitignore configured at {target_gitignore}.")
        return True
    except IOError as e:
        print(f"Failed to configure .gitignore: {e}")
        return False

def main():
    project_root = Path(__file__).resolve().parent.parent
    gitignore_source = project_root / ".gitignore"
    
    # If the .gitignore is not in the project root, try to find it relative to the script
    if not gitignore_source.exists():
        gitignore_source = Path(__file__).resolve().parent.parent / ".gitignore"

    if not initialize_git_repo(project_root):
        sys.exit(1)

    if gitignore_source.exists():
        if not configure_git_ignore(project_root, gitignore_source):
            sys.exit(1)
    else:
        print("Warning: No .gitignore source file found. Please create one manually.")

if __name__ == "__main__":
    main()