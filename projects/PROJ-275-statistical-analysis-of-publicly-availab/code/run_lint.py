"""
Linting and formatting execution script.
Runs flake8 for linting and black in check mode to ensure code style compliance.
"""
import subprocess
import sys
from pathlib import Path

def run_command(command: list[str]) -> int:
    """Run a shell command and stream output."""
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout)
    return result.returncode

def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    # Run flake8
    print("Running flake8 linting...")
    flake8_cmd = [sys.executable, "-m", "flake8", str(project_root)]
    if run_command(flake8_cmd) != 0:
        sys.exit("flake8 reported issues.")

    # Run black in check mode
    print("Running black formatting check...")
    black_cmd = [sys.executable, "-m", "black", "--check", str(project_root)]
    if run_command(black_cmd) != 0:
        sys.exit("black reported formatting issues.")

    print("Linting and formatting checks passed.")

if __name__ == "__main__":
    main()