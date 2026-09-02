import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run black formatter on the codebase."""
    code_root = Path(__file__).parent.parent
    black_cmd = [sys.executable, "-m", "black", "--check", str(code_root)]

    print(f"Running formatter check: {' '.join(black_cmd)}")
    try:
        result = subprocess.run(black_cmd, cwd=code_root, check=True)
        print("Formatting check passed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Formatting check failed. Run 'python -m black .' to fix.")
        return e.returncode
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it via 'pip install black'.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
