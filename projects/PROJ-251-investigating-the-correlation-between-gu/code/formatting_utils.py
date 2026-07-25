"""
Formatting utilities for running ruff and black on the project.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional

def run_command(command: list, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[bool, str]:
    """
    Run ruff check and fix on the code directory.
    Returns (success, message).
    """
    ruff_path = "ruff"
    
    # First, run check to see issues
    print(f"Running ruff check on {code_dir}...")
    returncode, stdout, stderr = run_command([ruff_path, "check", str(code_dir)])
    
    if returncode != 0:
        print("Ruff check found issues. Attempting to fix...")
        # Run ruff check --fix to automatically fix fixable issues
        returncode_fix, stdout_fix, stderr_fix = run_command(
            [ruff_path, "check", str(code_dir), "--fix"]
        )
        
        if returncode_fix != 0:
            print(f"Ruff fix completed with issues remaining:\n{stdout_fix}")
            return False, f"Ruff issues remain after fix attempt:\n{stdout_fix}"
        else:
            print("Ruff fix successful.")
            return True, "Ruff issues fixed."
    else:
        print("Ruff check passed.")
        return True, "No ruff issues found."

def run_black_format(code_dir: Path) -> Tuple[bool, str]:
    """
    Run black formatting on the code directory.
    Returns (success, message).
    """
    black_path = "black"
    
    print(f"Running black format on {code_dir}...")
    returncode, stdout, stderr = run_command([black_path, str(code_dir)])
    
    if returncode != 0:
        return False, f"Black formatting failed:\n{stderr}"
    
    print("Black formatting completed.")
    return True, "Black formatting successful."

def main():
    """
    Main entry point to run ruff and black on the code directory.
    """
    # Determine the project root (parent of 'code' directory)
    current_dir = Path.cwd()
    code_dir = current_dir / "code"
    
    if not code_dir.exists():
        print(f"Error: {code_dir} does not exist.")
        sys.exit(1)
    
    print("Starting code formatting and linting...")
    print("=" * 50)
    
    # Run ruff
    ruff_success, ruff_msg = run_ruff_check_and_fix(code_dir)
    print(ruff_msg)
    print("-" * 50)
    
    # Run black
    black_success, black_msg = run_black_format(code_dir)
    print(black_msg)
    print("=" * 50)
    
    if ruff_success and black_success:
        print("All formatting and linting checks passed.")
        sys.exit(0)
    else:
        print("Some formatting or linting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()