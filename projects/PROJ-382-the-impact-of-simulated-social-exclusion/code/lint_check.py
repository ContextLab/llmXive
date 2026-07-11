"""
Linting Compliance Verification Script.

This script runs flake8 and black --check to validate that the codebase
adheres to the project's linting standards defined in .flake8 and pyproject.toml.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """
    Run a shell command and report the result.

    Args:
        cmd: The command and arguments to run.
        description: A human-readable description of the check.

    Returns:
        True if the command succeeded, False otherwise.
    """
    print(f"Running: {description}...")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed.")
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"✗ {description} failed: Command not found. "
              f"Ensure '{cmd[0]}' is installed.")
        return False


def main() -> int:
    """
    Execute linting checks and return appropriate exit code.

    Returns:
        0 if all checks pass, 1 if any check fails.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        return 1

    # Change to project root so relative paths in configs work
    # and to match the scope of .flake8 / pyproject.toml
    try:
        import os
        os.chdir(project_root)
    except OSError as e:
        print(f"Error changing directory to {project_root}: {e}")
        return 1

    checks_passed = True

    # Run flake8
    if not run_command(
        ["flake8", "code/"],
        "Flake8 linting"
    ):
        checks_passed = False

    # Run black --check
    if not run_command(
        ["black", "--check", "code/"],
        "Black formatting check"
    ):
        checks_passed = False

    if checks_passed:
        print("\n✓ All linting checks passed.")
        return 0
    else:
        print("\n✗ Linting checks failed. Please fix the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())