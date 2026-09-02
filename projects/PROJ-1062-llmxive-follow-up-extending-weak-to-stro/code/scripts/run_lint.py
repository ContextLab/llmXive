import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run ruff linter on the codebase."""
    code_root = Path(__file__).parent.parent
    ruff_cmd = [sys.executable, "-m", "ruff", "check", str(code_root)]

    print(f"Running linter: {' '.join(ruff_cmd)}")
    try:
        result = subprocess.run(ruff_cmd, cwd=code_root, check=True)
        print("Linting passed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it via 'pip install ruff'.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
