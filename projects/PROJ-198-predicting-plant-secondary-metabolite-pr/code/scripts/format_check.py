"""
Legacy script for format checking, now delegating to run_lint_format.py.
Kept for backward compatibility.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Run a command."""
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main() -> None:
    """Run format check."""
    print("Running format check (Black)...")
    project_root = Path(__file__).parent.parent.parent
    try:
        run_command(["black", "--check", str(project_root)])
        print("✓ Format check passed.")
    except subprocess.CalledProcessError:
        print("✗ Format check failed. Run 'black .' to fix.")
        sys.exit(1)

if __name__ == "__main__":
    main()