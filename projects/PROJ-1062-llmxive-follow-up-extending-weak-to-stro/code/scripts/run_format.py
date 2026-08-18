"""
Script to run the formatter (black) on the project codebase.
Usage: python code/scripts/run_format.py
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run black format on the code directory."""
    root = Path(__file__).parent.parent.parent
    code_dir = root / "code"
    black_cmd = [sys.executable, "-m", "black", str(code_dir)]

    print(f"Running: {' '.join(black_cmd)}")
    try:
        result = subprocess.run(
            black_cmd,
            cwd=root,
            check=True,
            capture_output=False,
        )
        print("Formatting completed.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(main())
