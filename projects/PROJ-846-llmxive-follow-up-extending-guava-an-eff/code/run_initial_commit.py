import subprocess
import sys
from pathlib import Path
from code.git_operations import run_git_command
from code.init_git_repo import initialize_git_repository


def main():
    """
    Orchestrates the initial commit process.
    """
    project_root = Path.cwd()
    
    print("Starting initial commit process...")
    
    # 1. Initialize Git and Commit
    if not initialize_git_repository(project_root):
        print("Failed to initialize git repository.")
        sys.exit(1)
    
    # 2. Verify .git directory
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("Verification failed: .git directory does not exist.")
        sys.exit(1)
    
    # 3. Verify commit history
    stdout, stderr, code = run_git_command(["git", "log", "--oneline", "-1"], cwd=project_root)
    if code != 0 or not stdout.strip():
        print("Verification failed: No commit history found.")
        print(f"Stderr: {stderr}")
        sys.exit(1)
    
    print(f"Verification successful: Commit found - {stdout.strip()}")
    print("Initial commit process completed successfully.")


if __name__ == "__main__":
    main()