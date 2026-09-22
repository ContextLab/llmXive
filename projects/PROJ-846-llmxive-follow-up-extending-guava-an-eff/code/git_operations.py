import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

def run_git_command(command: list[str], cwd: Optional[Path] = None) -> tuple[int, str, str]:
    """
    Execute a git command and return (return_code, stdout, stderr).
    
    Args:
        command: List of git command arguments (e.g., ['add', '.'])
        cwd: Working directory for the command. Defaults to current directory.
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    full_command = ['git'] + command
    try:
        result = subprocess.run(
            full_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        print("Error: Git is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error executing git command: {e}", file=sys.stderr)
        sys.exit(1)

def stage_all_files(cwd: Optional[Path] = None) -> bool:
    """
    Stage all files in the repository using 'git add .'.
    
    Args:
        cwd: Working directory. Defaults to current directory.
        
    Returns:
        True if successful, False otherwise.
    """
    if cwd is None:
        cwd = Path.cwd()
        
    print(f"Staging all files in {cwd}...")
    returncode, stdout, stderr = run_git_command(['add', '.'], cwd)
    
    if returncode == 0:
        print("Successfully staged all files.")
        if stdout:
            print(stdout)
        return True
    else:
        print(f"Failed to stage files. Error: {stderr}", file=sys.stderr)
        return False

def commit_changes(message: str, cwd: Optional[Path] = None) -> bool:
    """
    Commit staged changes with the provided message.
    
    Args:
        message: Commit message.
        cwd: Working directory. Defaults to current directory.
        
    Returns:
        True if successful, False otherwise.
    """
    if cwd is None:
        cwd = Path.cwd()
        
    print(f"Committing changes with message: '{message}'...")
    returncode, stdout, stderr = run_git_command(['commit', '-m', message], cwd)
    
    if returncode == 0:
        print("Successfully committed changes.")
        if stdout:
            print(stdout)
        return True
    else:
        print(f"Failed to commit changes. Error: {stderr}", file=sys.stderr)
        return False

def add_remote(name: str, url: str, cwd: Optional[Path] = None) -> bool:
    """
    Add a remote repository.
    
    Args:
        name: Name of the remote (e.g., 'origin').
        url: URL of the remote repository.
        cwd: Working directory. Defaults to current directory.
        
    Returns:
        True if successful, False otherwise.
    """
    if cwd is None:
        cwd = Path.cwd()
        
    print(f"Adding remote '{name}' with URL '{url}'...")
    returncode, stdout, stderr = run_git_command(['remote', 'add', name, url], cwd)
    
    if returncode == 0:
        print(f"Successfully added remote '{name}'.")
        if stdout:
            print(stdout)
        return True
    else:
        # Check if remote already exists
        if "remote 'origin' already exists" in stderr:
            print(f"Remote '{name}' already exists. Skipping.")
            return True
        print(f"Failed to add remote. Error: {stderr}", file=sys.stderr)
        return False

def main() -> None:
    """
    Main entry point for git operations script.
    Demonstrates staging files, committing, and adding a remote.
    """
    # Example usage:
    # 1. Stage all files
    if not stage_all_files():
        print("Stopping: Failed to stage files.")
        sys.exit(1)
        
    # 2. Commit changes
    # Note: In a real scenario, you would check if there are changes to commit
    # For this task, we assume there are changes from previous setup tasks
    if not commit_changes("Initial commit"):
        print("Stopping: Failed to commit changes.")
        sys.exit(1)
        
    # 3. Add a remote (example URL, can be configured via arguments or env)
    # This is often done separately, but included here for completeness
    # remote_url = os.getenv('GIT_REMOTE_URL', 'https://github.com/example/repo.git')
    # add_remote('origin', remote_url)

if __name__ == '__main__':
    main()