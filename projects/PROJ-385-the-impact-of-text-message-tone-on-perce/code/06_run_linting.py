"""
Script to run linting and formatting checks on the codebase.

Executes ruff and black checks and reports the results.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list) -> int:
    """Run a command and return the exit code."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return 1

def main():
    """Main entry point for linting."""
    code_dir = Path(__file__).parent
    project_root = code_dir.parent
    
    print("Running ruff check...")
    ruff_code = run_command(["ruff", "check", str(code_dir)])
    
    print("\nRunning black check...")
    black_code = run_command(["black", "--check", str(code_dir)])
    
    if ruff_code == 0 and black_code == 0:
        print("\nAll linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\nSome checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()