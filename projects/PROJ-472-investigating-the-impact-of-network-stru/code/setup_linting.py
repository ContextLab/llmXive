"""
Script to initialize the linting and formatting environment.
This script installs pre-commit hooks and validates the configuration.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and print status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    project_root = Path(__file__).parent
    print(f"Configuring linting tools in: {project_root}")

    # 1. Install pre-commit if not present
    print("Ensuring pre-commit is installed...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pre-commit"], check=False)

    # 2. Install git hooks
    success = run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks"
    )

    if not success:
        print("Warning: Could not install pre-commit hooks. Run 'pre-commit install' manually.")
        return

    # 3. Run a dry-run check to verify config
    print("\nVerifying configuration with a dry run...")
    run_command(
        ["pre-commit", "run", "--all-files"],
        "Running pre-commit dry run"
    )

    print("\nLinting and formatting configuration complete.")
    print("To run manually: pre-commit run --all-files")

if __name__ == "__main__":
    main()
