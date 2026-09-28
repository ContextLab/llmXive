import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo(root_path: Path) -> None:
    """
    Initialize a git repository in the specified root path.
    Raises RuntimeError if initialization fails.
    """
    try:
        subprocess.run(
            ["git", "init"],
            cwd=root_path,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Git repository initialized at {root_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to initialize git repository: {e.stderr}")

def verify_git_repo(root_path: Path) -> bool:
    """
    Verify that a git repository exists in the specified root path.
    Returns True if .git directory exists and git status is valid.
    """
    git_dir = root_path / ".git"
    if not git_dir.exists():
        return False

    try:
        result = subprocess.run(
            ["git", "status"],
            cwd=root_path,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """
    Main entry point for initializing and verifying the git repository.
    Writes the git status to data/results/git_status.log.
    """
    root_path = Path(__file__).resolve().parent.parent
    results_dir = root_path / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    log_file = results_dir / "git_status.log"

    try:
        # Initialize the repository
        initialize_git_repo(root_path)

        # Verify the repository
        if not verify_git_repo(root_path):
            raise RuntimeError("Git verification failed after initialization.")

        # Capture git status
        result = subprocess.run(
            ["git", "status"],
            cwd=root_path,
            check=True,
            capture_output=True,
            text=True
        )

        # Write status to log file
        with open(log_file, "w") as f:
            f.write("Git Repository Initialization Status\n")
            f.write("=" * 40 + "\n")
            f.write(f"Path: {root_path}\n")
            f.write(f"Status:\n{result.stdout}")

        print(f"Git status logged to {log_file}")

    except Exception as e:
        # Log error to file as well
        with open(log_file, "w") as f:
            f.write(f"Error: {str(e)}\n")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
