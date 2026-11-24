"""
Run linting and formatting checks for the project.

This script executes:
  - `ruff check . --output-format=json` and writes the output to
    `artifacts/ruff_report.json`.
  - `black --check .` and writes the output to
    `artifacts/black_report.txt`.

Both commands must exit with status 0; otherwise the script exits with
a non‑zero code to signal failure.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, output_path):
    """Run a shell command and write its stdout+stderr to output_path."""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,  # handle returncode manually
        )
    except FileNotFoundError as e:
        print(f"Command not found: {command[0]}", file=sys.stderr)
        raise

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write captured output
    output_path.write_text(result.stdout)

    return result.returncode

def main():
    # Define output artifact paths
    ruff_output = Path("artifacts") / "ruff_report.json"
    black_output = Path("artifacts") / "black_report.txt"

    # Run ruff
    ruff_cmd = ["ruff", "check", ".", "--output-format=json"]
    ruff_rc = run_command(ruff_cmd, ruff_output)
    if ruff_rc != 0:
        print(f"Ruff reported violations (exit code {ruff_rc}). See {ruff_output}", file=sys.stderr)
        sys.exit(1)

    # Run black
    black_cmd = ["black", "--check", "."]
    black_rc = run_command(black_cmd, black_output)
    if black_rc != 0:
        print(f"Black reported formatting differences (exit code {black_rc}). See {black_output}", file=sys.stderr)
        sys.exit(1)

    print("Linting and formatting checks passed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()