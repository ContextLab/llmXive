"""
Utility functions for running formatting and linting tools.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional

def run_command(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return the return code, stdout, and stderr.

    Args:
        cmd: List of command arguments.
        cwd: Working directory for the command.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -2, "", f"Command not found: {cmd[0]}"

def run_ruff_check_and_fix(path: Path) -> Tuple[bool, str]:
    """
    Run ruff check and attempt to fix issues.

    Args:
        path: Path to the directory or file to check.

    Returns:
        Tuple of (success, message)
    """
    # Run fix first
    code, stdout, stderr = run_command(["ruff", "check", "--fix", str(path)])
    if code == 2:
        return False, f"Ruff check failed to run: {stderr}"

    # Run check again to see if issues remain
    code, stdout, stderr = run_command(["ruff", "check", str(path)])
    if code == 0:
        return True, "All ruff issues fixed or none present."
    elif code == 1:
        return False, f"Ruff issues remain:\n{stdout}"
    else:
        return False, f"Ruff check error: {stderr}"

def run_black_format(path: Path, check_only: bool = False) -> Tuple[bool, str]:
    """
    Run black formatting on a path.

    Args:
        path: Path to the directory or file to format.
        check_only: If True, only check formatting without modifying files.

    Returns:
        Tuple of (success, message)
    """
    cmd = ["black", str(path)]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")

    code, stdout, stderr = run_command(cmd)
    if code == 0:
        return True, "Black formatting check passed."
    elif code == 1:
        if check_only:
            return False, f"Black formatting issues found:\n{stdout}"
        else:
            return True, "Black formatting applied."
    else:
        return False, f"Black error: {stderr}"

def main():
    """Main entry point for formatting utilities."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    print("Running Ruff check and fix...")
    success, msg = run_ruff_check_and_fix(code_dir)
    print(msg)

    print("\nRunning Black format...")
    success, msg = run_black_format(code_dir)
    print(msg)

if __name__ == "__main__":
    main()
