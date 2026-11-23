import subprocess
import sys
import os
from pathlib import Path

def run_command(command: list, description: str) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {description}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {description}:\n{result.stderr}", file=sys.stderr)
    else:
        print(result.stdout)
    return result.returncode

def main():
    """Run linting and formatting checks."""
    # Ruff
    rc = run_command(["ruff", "--quiet", "."], "ruff lint")
    if rc != 0:
        sys.exit(rc)

    # Black check
    rc = run_command(["black", "--check", "."], "black format check")
    sys.exit(rc)

if __name__ == "__main__":
    main()
