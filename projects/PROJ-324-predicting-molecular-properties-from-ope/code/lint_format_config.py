"""
Linting and formatting configuration and execution utilities.

This module provides functions to run ruff (linting) and black (formatting)
on the project codebase, check for issues, and apply fixes automatically.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Configuration constants
RUFF_COMMAND = "ruff"
BLACK_COMMAND = "black"
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

def run_command(command: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and return the result.

    Args:
        command: List of command arguments.
        cwd: Working directory for the command.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {command[0]}"
    except Exception as e:
        return -1, "", str(e)

def check_code() -> Tuple[int, str]:
    """
    Run ruff to check for linting errors and black to check formatting.

    Returns:
        Tuple of (exit_code, message)
    """
    messages = []
    exit_code = 0

    # Run ruff check
    ruff_return, ruff_out, ruff_err = run_command([RUFF_COMMAND, "check", str(CODE_DIR), str(TESTS_DIR)])
    if ruff_return != 0:
        exit_code = 1
        messages.append("Ruff check found issues:")
        if ruff_out:
            messages.append(ruff_out)
        if ruff_err:
            messages.append(ruff_err)
    else:
        messages.append("Ruff check passed.")

    # Run black check (diff mode)
    black_return, black_out, black_err = run_command([BLACK_COMMAND, "--check", str(CODE_DIR), str(TESTS_DIR)])
    if black_return != 0:
        exit_code = 1
        messages.append("Black formatting check found issues:")
        if black_out:
            messages.append(black_out)
        if black_err:
            messages.append(black_err)
    else:
        messages.append("Black formatting check passed.")

    return exit_code, "\n".join(messages)

def fix_code() -> Tuple[int, str]:
    """
    Run ruff to auto-fix linting issues and black to format code.

    Returns:
        Tuple of (exit_code, message)
    """
    messages = []
    exit_code = 0

    # Run ruff check --fix
    ruff_return, ruff_out, ruff_err = run_command([RUFF_COMMAND, "check", "--fix", str(CODE_DIR), str(TESTS_DIR)])
    if ruff_return != 0 and ruff_return != 1:  # 1 is expected if issues remain after fix
        exit_code = ruff_return
        messages.append("Ruff fix encountered an error:")
        if ruff_err:
            messages.append(ruff_err)
    else:
        messages.append("Ruff fix completed.")
        if ruff_out:
            messages.append(ruff_out)

    # Run black
    black_return, black_out, black_err = run_command([BLACK_COMMAND, str(CODE_DIR), str(TESTS_DIR)])
    if black_return != 0:
        exit_code = black_return
        messages.append("Black formatting encountered an error:")
        if black_err:
            messages.append(black_err)
    else:
        messages.append("Black formatting completed.")
        if black_out:
            messages.append(black_out)

    return exit_code, "\n".join(messages)

def main() -> int:
    """
    Main entry point for CLI usage.

    Usage:
        python code/lint_format_config.py [check|fix]

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if len(sys.argv) < 2:
        print("Usage: python code/lint_format_config.py [check|fix]")
        print("  check: Run linters and formatters in check mode")
        print("  fix:   Run linters and formatters in fix mode")
        return 1

    mode = sys.argv[1].lower()

    if mode == "check":
        exit_code, message = check_code()
        print(message)
        return exit_code
    elif mode == "fix":
        exit_code, message = fix_code()
        print(message)
        return exit_code
    else:
        print(f"Unknown mode: {mode}. Use 'check' or 'fix'.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
