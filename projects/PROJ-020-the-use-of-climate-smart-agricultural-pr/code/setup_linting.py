"""
Linting and Formatting Setup Script.

This script ensures that ruff and black are properly configured and
runs them against the codebase to enforce style compliance.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}. Please ensure tools are installed.")
        return False

def main() -> int:
    """Main entry point for linting and formatting setup."""
    print("=" * 60)
    print("Linting and Formatting Compliance Check")
    print("=" * 60)

    # Ensure we are in the code directory
    os.chdir(Path(__file__).parent)

    # Check if ruff is installed
    if not run_command(["ruff", "--version"], "Checking ruff installation"):
        print("Error: ruff is not installed. Install with: pip install ruff")
        return 1

    # Check if black is installed
    if not run_command(["black", "--version"], "Checking black installation"):
        print("Error: black is not installed. Install with: pip install black")
        return 1

    print("\n" + "=" * 60)
    print("Step 1: Running Ruff Check (Linting)")
    print("=" * 60)
    ruff_check_success = run_command(
        ["ruff", "check", "code/"],
        "Ruff check"
    )

    if not ruff_check_success:
        print("\nRuff found issues. Attempting to fix auto-fixable issues...")
        # Try to fix what ruff can fix automatically
        fix_success = run_command(
            ["ruff", "check", "code/", "--fix"],
            "Ruff fix"
        )
        if not fix_success:
            print("Warning: Ruff fix did not resolve all issues or failed.")
            # Re-run check to see current state
            run_command(["ruff", "check", "code/"], "Final Ruff check")

    print("\n" + "=" * 60)
    print("Step 2: Running Black (Formatting)")
    print("=" * 60)
    black_success = run_command(
        ["black", "code/"],
        "Black formatting"
    )

    if not black_success:
        print("Warning: Black formatting encountered issues.")
        return 1

    print("\n" + "=" * 60)
    print("Step 3: Final Verification")
    print("=" * 60)
    final_check = run_command(
        ["ruff", "check", "code/"],
        "Final Ruff verification"
    )

    if not final_check:
        print("\nFinal verification failed. Some issues may require manual resolution.")
        # Run one last time to show output
        run_command(["ruff", "check", "code/"], "Final Ruff output")
        return 1

    print("\n" + "=" * 60)
    print("SUCCESS: Code style compliance verified.")
    print("All files in code/ pass ruff and black checks.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())