"""
Linting and formatting utilities for the BCC Yield Strength project.
Provides command-line interfaces to run Ruff and Black.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: list, description: str) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}. Please ensure '{command[0]}' is installed.", file=sys.stderr)
        return 1

def main():
    """
    Main entry point for linting and formatting.
    Usage: python -m code.lint_format [check|fix]
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.lint_format [check|fix]")
        print("  check: Run linters/formatters in check mode (fail if issues exist)")
        print("  fix:   Run linters/formatters in fix mode (apply changes)")
        sys.exit(1)

    mode = sys.argv[1]
    if mode not in ("check", "fix"):
        print(f"Invalid mode: {mode}. Use 'check' or 'fix'.")
        sys.exit(1)

    # Determine arguments based on mode
    ruff_args = ["ruff", "check", "code", "tests"] if mode == "check" else ["ruff", "check", "code", "tests", "--fix"]
    black_args = ["black", "--check", "code", "tests"] if mode == "check" else ["black", "code", "tests"]

    ruff_exit = run_command(ruff_args, "Ruff Linting")
    black_exit = run_command(black_args, "Black Formatting")

    if ruff_exit != 0 or black_exit != 0:
        print("\nLinting/Formatting failed.")
        sys.exit(1)

    print("\nLinting/Formatting successful.")
    sys.exit(0)

if __name__ == "__main__":
    main()
