"""
verify_linting.py
-----------------
Script to verify that the linting and formatting tools specified in
``code/requirements.txt`` are installed and functional.

It performs the following steps:
  1. Installs the project's requirements (including ``ruff`` and ``black``)
     using the current Python interpreter.
  2. Checks that ``ruff --version`` and ``black --version`` execute
     without error.
  3. Exits with status code 0 on success, non‑zero on any failure.

This script satisfies the verification requirement for task **T001a**.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command: list[str]) -> int:
    """Run a command and return its exit code."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(
                f"Command {' '.join(command)} failed with exit code {result.returncode}",
                file=sys.stderr,
            )
            print("Stdout:", result.stdout, file=sys.stderr)
            print("Stderr:", result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Executable not found: {command[0]}", file=sys.stderr)
        return 1

def main() -> int:
    # Step 1: install requirements
    req_path = Path(__file__).parent / "requirements.txt"
    if not req_path.is_file():
        print(f"Requirements file not found at {req_path}", file=sys.stderr)
        return 1

    print(f"Installing requirements from {req_path}...")
    pip_cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    if run_command(pip_cmd) != 0:
        return 1

    # Step 2: verify ruff
    print("Verifying ruff installation...")
    if run_command(["ruff", "--version"]) != 0:
        return 1

    # Step 3: verify black
    print("Verifying black installation...")
    if run_command(["black", "--version"]) != 0:
        return 1

    print("All linting/formatting tools are installed and functional.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
