"""
Helper script to run linting and formatting checks for the project.
Executes:
  - ruff check code/
  - black --check code/
Exits with a non‑zero status if any check fails.
"""
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd: list[str]) -> None:
    """Run a command and raise if it fails."""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stdout)
        sys.exit(result.returncode)

def main() -> None:
    """Run ruff and black checks."""
    project_root = Path(__file__).resolve().parent.parent
    # Ensure we are running from the project root
    cwd = str(project_root)

    # Run ruff
    run_cmd(["ruff", "check", "code/"],)

    # Run black
    run_cmd(["black", "--check", "code/"],)

if __name__ == "__main__":
    main()