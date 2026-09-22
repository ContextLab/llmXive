import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and print it."""
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def main():
    """Initialize pre-commit hooks for the project."""
    project_root = Path(__file__).parent.parent

    # Initialize git if not already done
    if not (project_root / ".git").exists():
        print("Initializing git repository...")
        run_command(["git", "init"], cwd=project_root)

    # Install pre-commit if not present
    print("Checking for pre-commit...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "pre-commit"],
                     check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("Installing pre-commit...")
        run_command([sys.executable, "-m", "pip", "install", "pre-commit"])

    # Install pre-commit hooks
    print("Installing pre-commit hooks...")
    success = run_command([sys.executable, "-m", "pre_commit", "install"], cwd=project_root)

    if success:
        print("Pre-commit hooks installed successfully.")
        print("Run 'pre-commit run --all-files' to check all files now.")
    else:
        print("Failed to install pre-commit hooks.")
        sys.exit(1)

if __name__ == "__main__":
    main()