"""
Linting tool wrapper for Ruff.
"""
import subprocess
import sys
from pathlib import Path


def run_command(directory: Path) -> int:
    """Run ruff on the given directory."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=directory,
        )
        print(f"Linting passed in {directory}.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Linting failed: {e}")
        return 1
    except FileNotFoundError:
        print("Ruff is not installed. Run: pip install ruff")
        return 1


def main():
    """Entry point for linting."""
    root = Path(__file__).resolve().parent.parent
    exit_code = run_command(root)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
