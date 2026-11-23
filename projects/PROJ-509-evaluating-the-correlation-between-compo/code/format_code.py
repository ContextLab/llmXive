"""
Script to format all Python files in the code/ directory using Black.
Enforces a line length of 88 characters as per task T049b.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Run Black formatter on the code directory."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Directory {code_dir} does not exist.")
        sys.exit(1)

    print(f"Formatting Python files in {code_dir} with line-length=88...")

    try:
        # Run black with the specified line length
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "black",
                "--line-length",
                "88",
                "--target-version",
                "py39",
                str(code_dir),
            ],
            check=True,
            capture_output=False,
        )
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during formatting: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'black' is not installed. Please install it via requirements.txt.")
        sys.exit(1)


if __name__ == "__main__":
    main()