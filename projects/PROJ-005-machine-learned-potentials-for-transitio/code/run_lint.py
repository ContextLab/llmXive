import subprocess
import sys
from pathlib import Path

def main():
    """Run flake8 and black checks on the project."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("=== Running Linting and Formatting Checks ===")

    # Run flake8
    print("\n--- Running flake8 ---")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "code/", "tests/"],
            check=False,
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print("\nFlake8 found issues.")
        else:
            print("Flake8 passed.")
    except FileNotFoundError:
        print("Error: flake8 not found. Please run 'setup_linting.py' first.")
        sys.exit(1)

    # Run black check
    print("\n--- Running black --check ---")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "code/", "tests/"],
            check=False,
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print("\nBlack formatting issues found. Run 'black code/ tests/' to fix.")
        else:
            print("Black formatting check passed.")
    except FileNotFoundError:
        print("Error: black not found. Please run 'setup_linting.py' first.")
        sys.exit(1)

    print("\n=== Linting Checks Complete ===")

if __name__ == "__main__":
    import os
    main()