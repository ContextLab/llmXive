import subprocess
import sys
from pathlib import Path

def main():
    """Run black formatter on the codebase."""
    code_dir = Path("code")
    if not code_dir.exists():
        print(f"Error: Directory {code_dir} does not exist.")
        sys.exit(1)

    print("Running black formatter...")
    result = subprocess.run(
        [sys.executable, "-m", "black", str(code_dir)],
        capture_output=False
    )

    if result.returncode != 0:
        print("Black formatting failed. Please check the errors above.")
        sys.exit(result.returncode)

    print("Black formatting completed successfully.")

if __name__ == "__main__":
    main()