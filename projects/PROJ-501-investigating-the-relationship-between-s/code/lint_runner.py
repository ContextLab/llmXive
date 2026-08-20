"""
Runner script to execute linting (flake8, pylint) and formatting (black) checks.
This script is intended to be run from the project root or code/ directory.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ {description} passed.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with return code {e.returncode}\n")
        return False

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    # Ensure we are in the right directory context
    if not code_dir.exists():
        print(f"Error: code/ directory not found at {code_dir}")
        sys.exit(1)

    all_passed = True

    # 1. Black (Formatting)
    # Check if black is installed
    try:
        subprocess.run(["black", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: 'black' not found in PATH. Skipping formatting check.")
        print("Install with: pip install black")
    else:
        # Run black in check mode (does not modify files)
        if not run_command(
            ["black", "--check", "--config", str(code_dir / "pyproject.toml"), str(code_dir)],
            "Black formatting check"
        ):
            all_passed = False

    # 2. Flake8 (Linting)
    try:
        subprocess.run(["flake8", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: 'flake8' not found in PATH. Skipping flake8 check.")
        print("Install with: pip install flake8")
    else:
        if not run_command(
            ["flake8", "--config", str(code_dir / ".flake8"), str(code_dir)],
            "Flake8 linting check"
        ):
            all_passed = False

    # 3. Pylint (Deep Linting)
    try:
        subprocess.run(["pylint", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: 'pylint' not found in PATH. Skipping pylint check.")
        print("Install with: pip install pylint")
    else:
        # Pylint usually exits with non-zero if issues are found based on config
        # We run it and let the return code determine success/failure
        cmd = [
            "pylint",
            "--rcfile=" + str(code_dir / ".pylintrc"),
            str(code_dir)
        ]
        if not run_command(cmd, "Pylint analysis"):
            all_passed = False

    if all_passed:
        print("All linting and formatting checks passed successfully.")
        sys.exit(0)
    else:
        print("One or more checks failed. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
