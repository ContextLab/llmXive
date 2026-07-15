"""
Formatting and linting runner for the project.

This script runs `ruff check` and `black` on the `code/` directory
to ensure code style compliance and fix any linting errors.

Usage:
    python code/run_formatting.py
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: list[str], cwd: Path | None = None) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {command[0]}")
        print("Please ensure 'ruff' and 'black' are installed.")
        return 1

def main() -> int:
    """Main entry point for the formatting runner."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Code directory not found: {code_dir}")
        return 1
    
    print(f"Running formatting and linting on: {code_dir}")
    print("=" * 60)
    
    # Run ruff check first
    ruff_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    ruff_exit = run_command(ruff_cmd, project_root)
    
    if ruff_exit != 0:
        print("\nRuff check found issues. Attempting to fix with ruff check --fix...")
        ruff_fix_cmd = [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)]
        ruff_fix_exit = run_command(ruff_fix_cmd, project_root)
        
        if ruff_fix_exit != 0:
            print("\nRuff check --fix did not resolve all issues.")
            print("Some issues may require manual intervention.")
        else:
            print("\nRuff check --fix resolved all fixable issues.")
    
    print("\n" + "=" * 60)
    
    # Run black
    black_cmd = [sys.executable, "-m", "black", str(code_dir)]
    black_exit = run_command(black_cmd, project_root)
    
    if black_exit != 0:
        print("\nBlack formatting failed.")
        return 1
    
    print("\n" + "=" * 60)
    print("Formatting and linting completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())