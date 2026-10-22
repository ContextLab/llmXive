"""
Script to create a Python 3.11 virtual environment in the project root.

The script performs the following steps:
1. Invokes `python3.11 -m venv venv` to create the environment if it does not already exist.
2. Verifies that the created interpreter reports a Python 3.11.x version.
3. Exits with status 0 on success, or a non‑zero status with an error message on failure.

This satisfies task T002a which requires the `venv/` directory to be present and
`venv/bin/python --version` to return a Python 3.11.x string.
"""

import subprocess
import sys
import os
from pathlib import Path

def _run_command(command, **kwargs):
    """Run a command, raising on non‑zero exit."""
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        **kwargs,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, command, output=result.stdout
        )
    return result.stdout.strip()

def main():
    project_root = Path(__file__).resolve().parent.parent  # project root directory
    venv_path = project_root / "venv"

    # Step 1: Create the venv if it does not exist
    if not venv_path.is_dir():
        try:
            print(f"Creating virtual environment at {venv_path} using python3.11...")
            _run_command(["python3.11", "-m", "venv", str(venv_path)])
        except Exception as exc:
            print(f"ERROR: Failed to create virtual environment: {exc}")
            sys.exit(1)
    else:
        print(f"Virtual environment already exists at {venv_path}")

    # Step 2: Verify the interpreter version inside the venv
    venv_python = venv_path / "bin" / "python"
    if not venv_python.is_file():
        print(f"ERROR: Expected interpreter not found at {venv_python}")
        sys.exit(1)

    try:
        version_output = _run_command([str(venv_python), "--version"])
    except Exception as exc:
        print(f"ERROR: Could not run {venv_python} --version: {exc}")
        sys.exit(1)

    # The output is typically "Python 3.11.x"
    if not version_output.startswith("Python 3.11"):
        print(f"ERROR: Unexpected Python version: '{version_output}'. Expected a 3.11.x interpreter.")
        sys.exit(1)

    print(f"Virtual environment created successfully. {venv_python} reports: {version_output}")
    sys.exit(0)

if __name__ == "__main__":
    main()