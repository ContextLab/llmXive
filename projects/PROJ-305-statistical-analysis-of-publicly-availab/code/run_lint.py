"""Run linting and formatting checks and capture their output.

This script executes `ruff check .` and `black --check .`, writes the combined
stdout/stderr to `logs/lint.txt`, and exits with the return code of the first
failing command (or 0 if both succeed).
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def _run_command(command: list[str]) -> subprocess.CompletedProcess:
    """Execute a command, returning the completed process."""
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

def main() -> None:
    """Execute ruff and black checks, writing their output to logs/lint.txt."""
    log_file: Path = paths.logs("lint.txt")
    commands = [
        ["ruff", "check", "."],
        ["black", "--check", "."],
    ]

    with log_file.open("w", encoding="utf-8") as out:
        for cmd in commands:
            out.write(f"$ {' '.join(cmd)}\n")
            result = _run_command(cmd)
            out.write(result.stdout)
            out.write("\n")
            if result.returncode != 0:
                # Exit immediately with the failing command's status code.
                sys.exit(result.returncode)

    # If we reach this point, both commands succeeded.
    sys.exit(0)

if __name__ == "__main__":
    main()
