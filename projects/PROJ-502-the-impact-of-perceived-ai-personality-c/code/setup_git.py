"""
Script to initialize a Git repository in the project root.
This script handles the initialization of the .git directory
and performs the initial commit for the project structure.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command to run (list of strings)
        cwd: Working directory
        check: Raise exception if command fails
        
    Returns:
        subprocess.CompletedProcess
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise

def is_git_repo(path):
    """Check if the given path is a Git repository."""
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()

def initialize_git_repository(project_root):
    """
    Initialize a Git repository in the project root.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    project_root = Path(project_root)
    
    if not project_root.exists():
        raise FileNotFoundError(f"Project root does not exist: {project_root}")
    
    if is_git_repo(project_root):
        print(f"Git repository already initialized at {project_root}")
        return True
    
    print(f"Initializing Git repository at {project_root}")
    
    # Initialize the repository
    result = run_command(["git", "init"], cwd=project_root)
    print(f"Git init output: {result.stdout}")
    
    # Configure user identity if not set (required for commit)
    # We set a generic identity for the automated pipeline
    run_command(["git", "config", "user.email", "llmxive@pipeline.local"], cwd=project_root, check=False)
    run_command(["git", "config", "user.name", "llmXive Pipeline"], cwd=project_root, check=False)
    
    # Create a .gitignore file if it doesn't exist
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Data
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep

# Output
output/figures/*
!output/figures/.gitkeep
output/reports/*
!output/reports/.gitkeep

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""
        gitignore_path.write_text(gitignore_content.strip())
        print(f"Created .gitignore at {gitignore_path}")
    
    # Create .gitkeep files in empty directories to ensure they are tracked
    dirs_to_keep = [
        "data/raw", "data/processed",
        "output/figures", "output/reports",
        "tests/unit", "tests/contract", "tests/integration"
    ]
    
    for dir_path in dirs_to_keep:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            keep_file = full_path / ".gitkeep"
            if not keep_file.exists():
                keep_file.write_text("# Keep directory in git\n")
                print(f"Created .gitkeep at {keep_file}")
    
    # Add all files
    print("Adding all files to Git...")
    run_command(["git", "add", "."], cwd=project_root)
    
    # Initial commit
    print("Creating initial commit...")
    commit_msg = "Initial project structure setup"
    result = run_command(["git", "commit", "-m", commit_msg], cwd=project_root)
    print(f"Commit output: {result.stdout}")
    
    print(f"Git repository successfully initialized at {project_root}")
    return True

def main():
    """Main entry point for the script."""
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    print(f"Project root detected at: {project_root}")
    
    try:
        success = initialize_git_repository(project_root)
        if success:
            print("Task T002b completed successfully.")
            sys.exit(0)
        else:
            print("Task T002b failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Task T002b failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()