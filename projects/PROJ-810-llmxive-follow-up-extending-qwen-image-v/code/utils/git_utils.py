import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

def check_git_initialized(repo_path: Path) -> bool:
    """Check if the given path is a git repository."""
    git_dir = repo_path / ".git"
    return git_dir.exists() and git_dir.is_dir()

def initialize_git_repository(repo_path: Path, initial_commit_message: str = "Initial commit: Project setup") -> Tuple[bool, Optional[str]]:
    """
    Initialize a git repository at the specified path if not already initialized.
    
    Args:
        repo_path: Path to the project root directory.
        initial_commit_message: Message for the initial commit.
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    repo_path = Path(repo_path).resolve()
    
    if not repo_path.exists():
        return False, f"Directory does not exist: {repo_path}"
    
    if check_git_initialized(repo_path):
        return True, None  # Already initialized
    
    try:
        # Initialize repository
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Configure user if not set (for initial commit)
        subprocess.run(
            ["git", "config", "user.name", "llmXive-bot"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        subprocess.run(
            ["git", "config", "user.email", "bot@llmxive.ai"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Add all files (excluding typical gitignored items if .gitignore exists)
        gitignore_path = repo_path / ".gitignore"
        if gitignore_path.exists():
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            # If no .gitignore, we still add everything
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
        
        # Create initial commit
        subprocess.run(
            ["git", "commit", "-m", initial_commit_message],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        return True, None
    
    except subprocess.CalledProcessError as e:
        return False, f"Git command failed: {e.stderr}"
    except FileNotFoundError:
        return False, "Git is not installed or not in PATH"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    """CLI entry point for git initialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize git repository for project")
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the project root directory (default: current directory)"
    )
    parser.add_argument(
        "--message",
        type=str,
        default="Initial commit: Project setup",
        help="Message for the initial commit"
    )
    
    args = parser.parse_args()
    
    repo_path = Path(args.path).resolve()
    success, error = initialize_git_repository(repo_path, args.message)
    
    if success:
        if error is None:
            print(f"Git repository already initialized at {repo_path}")
        else:
            print(f"Git repository initialized successfully at {repo_path}")
        return 0
    else:
        print(f"Failed to initialize git repository: {error}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())