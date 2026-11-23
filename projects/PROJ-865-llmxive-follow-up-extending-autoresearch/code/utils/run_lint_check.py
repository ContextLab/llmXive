"""
Helper script to run Ruff lint check specifically.
Used in CI or manual verification steps.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def main():
    """
    Runs ruff check on the code directory.
    Returns 0 if successful, 1 if linting issues found or error occurred.
    """
    cmd = [sys.executable, "-m", "ruff", "check", str(CODE_DIR)]
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        if result.returncode == 0:
            print("Ruff check passed.")
        else:
            print("Ruff check failed. Please fix linting errors.")
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: ruff not found. Install with: pip install ruff")
        sys.exit(1)
    except Exception as e:
        print(f"Error running ruff: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()