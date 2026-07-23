"""
Helper script to run Black check specifically.
Used in CI or manual verification steps.
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def run_black_check() -> int:
    """
    Runs black --check on the code directory.
    Returns 0 if successful, 1 if formatting issues found or error occurred.
    """
    cmd = [sys.executable, "-m", "black", "--check", str(CODE_DIR)]
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Install with: pip install black")
        return 1
    except Exception as e:
        print(f"Error running black: {e}")
        return 1

def main():
    exit_code = run_black_check()
    if exit_code == 0:
        print("Black check passed.")
    else:
        print("Black check failed. Run 'black code/' to fix.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
