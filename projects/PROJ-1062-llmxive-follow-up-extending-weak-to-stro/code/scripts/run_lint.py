"""
Script to run the linter (ruff) on the project codebase.
Usage: python code/scripts/run_lint.py
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run ruff check on the code directory."""
    root = Path(__file__).parent.parent.parent
    code_dir = root / "code"
    ruff_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]

    print(f"Running: {' '.join(ruff_cmd)}")
    try:
        result = subprocess.run(
            ruff_cmd,
            cwd=root,
            check=True,
            capture_output=False,
        )
        print("Linting passed.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(main())
