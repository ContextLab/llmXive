"""
Formatting tool wrapper for Black.
"""
import subprocess
import sys
from pathlib import Path


def run_command(directory: Path) -> int:
    """Run black on the given directory."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "black", "."],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"Formatted code in {directory} successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error formatting code: {e}")
        return 1
    except FileNotFoundError:
        print("Black is not installed. Run: pip install black")
        return 1


def main():
    """Entry point for formatting."""
    root = Path(__file__).resolve().parent.parent
    exit_code = run_command(root)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
