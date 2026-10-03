import os
import subprocess
import sys
from pathlib import Path
from code.git_operations import init_repository, stage_all_files, commit_changes


def initialize_git_repository(project_root: Path) -> bool:
    """
    Initialize the git repository, create .gitignore, stage, and commit.
    """
    gitignore_path = project_root / ".gitignore"
    
    # Ensure .gitignore exists (create if missing)
    if not gitignore_path.exists():
        # Create a default .gitignore if one doesn't exist
        # In a real scenario, this might be copied from a template
        default_gitignore = """
        *.pyc
        __pycache__/
        .env
        data/raw/*
        data/artifacts/*
        *.log
        *.pth
        """
        gitignore_path.write_text(default_gitignore.strip())
        print(f"Created default .gitignore at {gitignore_path}")
    
    # 1. Initialize Git
    print("Initializing Git repository...")
    if not init_repository(project_root):
        return False

    # 2. Stage all files
    print("Staging all files...")
    if not stage_all_files(project_root):
        return False

    # 3. Commit
    print("Committing initial state...")
    if not commit_changes(project_root, "Initial commit"):
        return False

    # Verify .git directory exists
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("Error: .git directory not found after initialization.")
        return False

    print("Git repository initialized successfully.")
    return True


def main():
    """
    Entry point for the script.
    Expects project root to be the current directory or passed via argument.
    """
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        project_root = Path.cwd()

    print(f"Target project root: {project_root}")
    
    success = initialize_git_repository(project_root)
    
    if not success:
        sys.exit(1)
    else:
        # Final verification
        stdout, _, _ = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=project_root,
            capture_output=True,
            text=True
        ).stdout, "", 0
        
        if stdout:
            print(f"Verification: Commit history contains entry: {stdout.strip()}")
        else:
            print("Warning: Could not verify commit history.")

if __name__ == "__main__":
    main()
