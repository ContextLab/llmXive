import subprocess
import sys
from pathlib import Path

def run_command(cmd: list) -> int:
    """Run a command and return the exit code."""
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return 1

def main():
    """Run linting and formatting checks."""
    print("Running linting and formatting checks...")
    
    # Check if tools are available
    ruff_code = run_command([sys.executable, "-m", "ruff", "check", "."])
    black_code = run_command([sys.executable, "-m", "black", "--check", "."])
    
    if ruff_code == 0 and black_code == 0:
        print("All checks passed!")
        return 0
    else:
        print("Some checks failed. Please fix the issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
