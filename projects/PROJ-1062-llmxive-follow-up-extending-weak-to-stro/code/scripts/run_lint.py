import subprocess
import sys
from pathlib import Path

def main():
    """Run ruff linter on the codebase."""
    code_dir = Path("code")
    if not code_dir.exists():
        print(f"Error: Directory {code_dir} does not exist.")
        sys.exit(1)

    print("Running ruff check...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=False
    )

    if result.returncode != 0:
        print("Ruff check failed. Please fix the issues above.")
        sys.exit(result.returncode)

    print("Ruff check passed.")

if __name__ == "__main__":
    main()
