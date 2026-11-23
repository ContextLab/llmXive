"""
run_lint.py: Execute linting and formatting checks.

This script runs `ruff check .` and `black --check .`, captures their
stdout/stderr, and writes the combined output to
`artifacts/metrics/lint_report.txt`. It exits with a non‑zero status if
either tool reports a problem.
"""

import subprocess
from pathlib import Path
import sys


def run_command(command: list[str]) -> str:
    """Run a command and return its combined stdout/stderr."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    # If the command failed, raise to propagate the error code.
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result.stdout + result.stderr


def main() -> None:
    # Ensure the output directory exists.
    output_path = Path("artifacts/metrics/lint_report.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        ruff_output = run_command(["ruff", "check", "."])
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Ruff failed:\n{e.stderr}\n")
        raise

    try:
        black_output = run_command(["black", "--check", "."])
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Black failed:\n{e.stderr}\n")
        raise

    combined = (
        "=== ruff check output ===\n"
        + ruff_output
        + "\n=== black --check output ===\n"
        + black_output
    )
    output_path.write_text(combined, encoding="utf-8")
    print(f"Lint and formatting report written to {output_path}")


if __name__ == "__main__":
    main()