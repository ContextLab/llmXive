import subprocess
import sys
from pathlib import Path
from config import get_project_root

def run_command(cmd: List[str]) -> int:
    """Runs a command and returns the exit code."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        return e.returncode

def main():
    """
    Main entry point for the quickstart linting script.
    """
    print("Running linting setup...")
    # Placeholder for actual linting commands
    return 0

if __name__ == "__main__":
    sys.exit(main())
