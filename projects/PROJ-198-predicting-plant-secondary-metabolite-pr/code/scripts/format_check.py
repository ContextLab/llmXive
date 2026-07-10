"""
Script to verify code formatting and linting compliance.
Runs ruff and black checks.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            check=False,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}. Please install dependencies.", file=sys.stderr)
        return 1

def main() -> int:
    """Main entry point."""
    print("Checking formatting and linting...")
    
    # Check black
    black_code = run_command(["black", "--check", "--config", ".black.toml", "code/"])
    
    # Check ruff
    ruff_code = run_command(["ruff", "check", "--config", ".ruff.toml", "code/"])
    
    if black_code == 0 and ruff_code == 0:
        print("\n✓ All checks passed!")
        return 0
    else:
        print("\n✗ Checks failed. Run 'black . && ruff check --fix .' to fix automatically.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
