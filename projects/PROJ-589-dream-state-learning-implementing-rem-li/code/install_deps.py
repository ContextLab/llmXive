"""
Dependency installation verification script.

This script invokes the project's pinned requirements file
(code/requirements.txt) via pip. Successful execution demonstrates
that the environment can resolve and install all declared dependencies,
satisfying the T001 verification criterion.

Usage (run from project root):
    python code/install_deps.py
"""
import subprocess
import sys
from pathlib import Path

def main() -> int:
    # Resolve the requirements file relative to this script
    requirements_path = Path(__file__).resolve().parent / "requirements.txt"

    if not requirements_path.is_file():
        print(f"Requirements file not found at {requirements_path}", file=sys.stderr)
        return 1

    # Construct the pip install command using the current interpreter
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]

    print(f"Running pip install for requirements: {requirements_path}")
    try:
        subprocess.check_call(cmd)
        print("Dependency installation completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Pip install failed with exit code {e.returncode}", file=sys.stderr)
        return e.returncode
    except Exception as exc:
        print(f"Unexpected error during pip install: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
