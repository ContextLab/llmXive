"""
Script to initialize and configure pre-commit hooks for the llmXive project.
This task (T003) ensures ruff and black are configured and pre-commit is initialized.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """
    Run a shell command and report success/failure.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"✓ {description} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point for T003: Configure linting (ruff) and formatting (black) tools with pre-commit hooks.
    """
    project_root = Path(__file__).parent.parent
    print(f"Initializing pre-commit hooks in: {project_root}\n")

    # 1. Install pre-commit if not present
    success = run_command(
        [sys.executable, "-m", "pip", "install", "-q", "pre-commit"],
        "Installing pre-commit package"
    )
    if not success:
        return 1

    # 2. Initialize pre-commit in the git repo (creates .git/hooks/pre-commit)
    success = run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hook script"
    )
    if not success:
        # If git is not initialized, this might fail, but we can still run manually
        print("Note: pre-commit install failed (likely no git repo). You can run 'pre-commit run --all-files' manually.\n")

    # 3. Run pre-commit on all files to ensure configuration is valid
    print("Running pre-commit on all files to validate configuration...")
    success = run_command(
        ["pre-commit", "run", "--all-files"],
        "Validating configuration with pre-commit run --all-files"
    )

    if success:
        print("✓ All pre-commit hooks passed. Configuration successful.")
        return 0
    else:
        print("⚠ Pre-commit run encountered issues. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
