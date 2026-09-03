import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """
    Run a command and return True if it succeeds (exit code 0).
    Prints output to stdout/stderr to allow immediate feedback.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {description} passed.\n")
            return True
        else:
            print(f"✗ {description} failed with exit code {result.returncode}.\n")
            return False
    except FileNotFoundError:
        print(f"✗ {description} failed: Command not found. Is the tool installed?\n")
        return False
    except Exception as e:
        print(f"✗ {description} failed with exception: {e}\n")
        return False

def main():
    """
    Entry point to run initial linting and formatting checks.
    Verifies ruff and black configuration on the project structure.
    """
    # Ensure we are running from the project root or handle path correctly
    # The script is expected to be run from the root where .ruff.toml and pyproject.toml exist.
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    
    print(f"Project root: {project_root}")
    print("-" * 40)

    checks = [
        (["ruff", "check", "."], "Ruff Linting"),
        (["black", "--check", "."], "Black Formatting Check"),
    ]

    all_passed = True
    for cmd, desc in checks:
        if not run_command(cmd, desc):
            all_passed = False

    print("-" * 40)
    if all_passed:
        print("All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("One or more checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
