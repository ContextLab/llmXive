"""
Script to verify that linting and formatting configurations are valid.
This helps ensure T003 is correctly implemented.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> bool:
    """Run a command and return True if successful."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✓ {' '.join(cmd)}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {' '.join(cmd)} failed")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    project_root = Path(__file__).parent.parent
    print(f"Checking linting configuration in {project_root}...")

    # Check if ruff is installed
    if not run_command(["ruff", "--version"]):
        print("Error: ruff is not installed. Run: pip install ruff")
        return 1

    # Check if black is installed
    if not run_command(["black", "--version"]):
        print("Error: black is not installed. Run: pip install black")
        return 1

    # Validate ruff config
    print("\nValidating Ruff configuration...")
    if not run_command(["ruff", "check", "--config", "pyproject.toml", "--no-fix", "."]):
        print("Warning: Ruff found issues. Run 'ruff check --fix' to auto-fix.")

    # Validate black config
    print("\nValidating Black configuration...")
    if not run_command(["black", "--config", "pyproject.toml", "--check", "."]):
        print("Warning: Black found formatting issues. Run 'black .' to auto-format.")

    print("\nLinting configuration check complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())