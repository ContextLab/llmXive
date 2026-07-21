"""
Configuration and execution utilities for Ruff linting and Black formatting.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result.

    Args:
        cmd: Command and arguments as a list.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        Tuple of (return_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def check_code() -> int:
    """
    Run Ruff check on the codebase.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    code_dir = Path(__file__).parent.parent / "code"
    cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    print(f"Running: {' '.join(cmd)}")
    returncode, stdout, stderr = run_command(cmd, check=False)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    return returncode


def fix_code() -> int:
    """
    Run Ruff check --fix and Black to format the codebase.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    code_dir = Path(__file__).parent.parent / "code"
    
    # Run Ruff fix
    print("Running Ruff fix...")
    ruff_cmd = [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)]
    returncode, stdout, stderr = run_command(ruff_cmd, check=False)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    
    # Run Black
    print("Running Black formatter...")
    black_cmd = [sys.executable, "-m", "black", str(code_dir)]
    returncode, stdout, stderr = run_command(black_cmd, check=False)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    
    return returncode


def main() -> int:
    """
    Main entry point for linting and formatting configuration.
    
    Usage:
        python code/lint_format_config.py check   -> Check code style
        python code/lint_format_config.py fix     -> Fix issues and format
    """
    if len(sys.argv) < 2:
        print("Usage: python code/lint_format_config.py [check|fix]")
        print("  check: Run linter to detect issues")
        print("  fix:   Run linter auto-fix and formatter")
        return 1
    
    action = sys.argv[1].lower()
    if action == "check":
        return check_code()
    elif action == "fix":
        return fix_code()
    else:
        print(f"Unknown action: {action}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
