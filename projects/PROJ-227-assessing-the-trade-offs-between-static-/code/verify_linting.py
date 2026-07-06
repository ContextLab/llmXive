"""
Verification script for T003: Configure linting and formatting.
Runs black --check and flake8 to ensure configuration is correct.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if it succeeds."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"✓ {description} passed")
            return True
        else:
            print(f"✗ {description} failed")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
    except FileNotFoundError:
        print(f"✗ {description} failed: Command not found")
        return False

def main() -> int:
    """Main entry point for verification."""
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")

    # Change to project root
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(project_root)

        # Run black check
        black_success = run_command(
            ["black", "--check", "."],
            "Black formatting check"
        )

        # Run flake8
        flake8_success = run_command(
            ["flake8", "."],
            "Flake8 linting check"
        )

        if black_success and flake8_success:
            print("\n✓ All linting and formatting checks passed!")
            return 0
        else:
            print("\n✗ Some checks failed.")
            return 1

    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    sys.exit(main())