"""
Script to verify linting (ruff) and formatting (black) configuration.
This script runs ruff check and black --check to ensure exit code 0.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> bool:
    """Run a command and return True if it succeeds."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        return False

def main() -> int:
    """Main entry point."""
    # Ensure we are in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")

    # Check if pyproject.toml exists
    if not os.path.exists("pyproject.toml"):
        print("ERROR: pyproject.toml not found in project root.")
        return 1

    # Run ruff check
    print("\n--- Running ruff check ---")
    ruff_success = run_command(["ruff", "check", "."])

    # Run black check
    print("\n--- Running black --check ---")
    black_success = run_command(["black", "--check", "."])

    if ruff_success and black_success:
        print("\n✅ Linting and formatting checks passed.")
        return 0
    else:
        print("\n❌ Linting or formatting checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())