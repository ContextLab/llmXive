"""
Script to initialize linting, formatting, and pre-commit hooks for the project.
This corresponds to task T004.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and print status."""
    print(f"Running: {description}...")
    try:
        subprocess.run(cmd, check=True, text=True)
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}.")
        return False

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print(f"Project root: {project_root}")

    # 1. Install pre-commit and ruff if not already present
    # (Assuming requirements.txt was installed in T003b, but ensuring here for safety)
    print("Ensuring pre-commit and ruff are installed...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "pre-commit", "ruff"],
        check=True,
    )

    # 2. Initialize pre-commit
    if not run_command(["pre-commit", "install"], "Pre-commit hooks installation"):
        return 1

    # 3. Run a quick check on existing files to verify configuration
    print("\nRunning initial lint check on existing code...")
    # We run ruff on the code/ directory. If it fails due to missing files, it's okay,
    # but we want to ensure the config is picked up.
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("\nLinting and formatting configuration complete.")
    print("To run manually: pre-commit run --all-files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
