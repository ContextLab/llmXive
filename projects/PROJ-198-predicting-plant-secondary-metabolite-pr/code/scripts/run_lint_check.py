"""
Script to run linting and formatting checks for the project.
Executes:
  - ruff --quiet .
  - black --check .
Exits with the same return code as the failing command, or 0 if both succeed.
"""
import subprocess
import sys

def main() -> None:
    try:
        # Run Ruff linter
        subprocess.check_call(["ruff", "--quiet", "."])
        # Run Black formatter in check mode
        subprocess.check_call(["black", "--check", "."])
    except subprocess.CalledProcessError as e:
        # Propagate the non-zero exit code
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()