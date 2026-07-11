"""
Utility script to run linting and formatting checks.
This script ensures the codebase adheres to the project's quality standards.

Usage:
    python code/lint_format.py check   # Run checks without fixing
    python code/lint_format.py fix     # Run checks and apply fixes
"""

import subprocess
import sys
import os

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {description} passed.")
            return True
        else:
            print(f"✗ {description} failed.")
            return False
    except FileNotFoundError:
        print(f"✗ Command not found: {cmd[0]}. Please ensure tools are installed.")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python code/lint_format.py [check|fix]")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode not in ("check", "fix"):
        print("Invalid mode. Use 'check' or 'fix'.")
        sys.exit(1)

    # Determine project root (assuming script is in code/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # 1. Ruff (Linting)
    ruff_cmd = ["ruff", "check", "."]
    if mode == "fix":
        ruff_cmd.append("--fix")
    
    ruff_ok = run_command(ruff_cmd, "Ruff Linting")

    # 2. Black (Formatting)
    black_cmd = ["black", "--check", "."]
    if mode == "fix":
        black_cmd = ["black", "."]
    
    black_ok = run_command(black_cmd, "Black Formatting")

    if ruff_ok and black_ok:
        print("\n✓ All checks passed.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed.")
        if mode == "check":
            print("Run 'python code/lint_format.py fix' to attempt automatic fixes.")
        sys.exit(1)

if __name__ == "__main__":
    main()