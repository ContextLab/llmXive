import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and print status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    """Initialize git repo, install pre-commit, and run initial scan."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # 1. Ensure git is initialized
    if not (project_root / ".git").exists():
        print("Initializing git repository...")
        if not run_command(["git", "init"], "Git init"):
            return False

    # 2. Install pre-commit if not present
    print("Checking/installing pre-commit...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-U", "pre-commit"], check=False)

    # 3. Install the git hook
    if not run_command(["pre-commit", "install"], "Pre-commit install"):
        print("Warning: pre-commit hook installation failed.")
        print("You may need to run 'pre-commit install' manually.")
        return False

    # 4. Run pre-commit on all files (optional, can be slow)
    print("Running pre-commit on all files (this may take a moment)...")
    # We use --all-files to scan everything, not just staged
    if not run_command(["pre-commit", "run", "--all-files"], "Pre-commit run --all-files"):
        print("Note: Some pre-commit checks may have failed. This is expected if the codebase is not yet fully formatted/linted.")
        print("Run 'pre-commit run --all-files' again after fixing issues.")

    print("\n✅ Pre-commit setup complete!")
    print("To run manually: pre-commit run --all-files")
    print("To run on commit: git commit")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)