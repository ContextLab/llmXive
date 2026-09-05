import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a shell command, raising an exception on failure."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=False, text=True
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(e.cmd)}") from e

def main() -> int:
    """Initialize pre-commit hooks for the project."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Initializing pre-commit in {project_root}...")

    # Ensure pre-commit is installed
    try:
        run_command([sys.executable, "-m", "pip", "install", "-q", "pre-commit"])
    except RuntimeError as e:
        print(f"Warning: Could not install pre-commit: {e}")
        print("Please install it manually: pip install pre-commit")
        return 1

    # Initialize git repo if not present (optional but helpful for standalone runs)
    if not (project_root / ".git").exists():
        print("Initializing git repository...")
        run_command(["git", "init"], cwd=project_root)

    # Install pre-commit hook
    print("Installing pre-commit hooks...")
    run_command(["pre-commit", "install"], cwd=project_root)

    # Run hooks on all files to ensure clean state
    print("Running pre-commit on all files...")
    run_command(["pre-commit", "run", "--all-files"], cwd=project_root)

    print("Pre-commit setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())