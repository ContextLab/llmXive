"""
Script to automatically format code using Black and fix linting issues using Ruff.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Run a shell command and raise if it fails."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)

def main() -> None:
    """Format code and fix linting issues."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    print("--- Formatting with Black ---")
    run_command(["black", str(code_dir)])

    print("\n--- Fixing with Ruff ---")
    run_command(["ruff", "check", "--fix", str(code_dir)])

    print("\nCode formatted and linted successfully.")

if __name__ == "__main__":
    main()
