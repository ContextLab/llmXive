import subprocess
import sys
from pathlib import Path
from config import get_project_root

def run_command(command: list, cwd: Path = None) -> bool:
    """Run a shell command and return success status."""
    try:
        subprocess.run(
            command,
            check=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        print(f"Error: {e.stderr.decode()}")
        return False

def main():
    """Main entry point for quickstart linting checks."""
    root = get_project_root()
    print(f"Running linting checks for project: {root}")

    checks = [
        (["ruff", "check", "code/"], "Ruff check on code/"),
        (["black", "--check", "code/"], "Black check on code/"),
    ]

    passed = 0
    failed = 0

    for cmd, description in checks:
        print(f"\nRunning: {description}")
        if run_command(cmd, root):
            print(f"✓ {description} passed")
            passed += 1
        else:
            print(f"✗ {description} failed")
            failed += 1

    print(f"\n--- Summary ---")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
