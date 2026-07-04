"""
Tool to run linter (ruff) and formatter (black) on the project codebase.
This script ensures code quality standards are met.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Execute a shell command and return success status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed.")
        print(f"Error output:\n{e.stderr}")
        return False

def main():
    """Main entry point for linting and formatting."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    print(f"Project root: {project_root}")
    print(f"Running tools for: {code_dir}, {tests_dir}\n")

    # 1. Format with Black
    # Using the version pinned in requirements.txt to ensure consistency
    format_cmd = [
        sys.executable, "-m", "black",
        "--config", str(project_root / "pyproject.toml"),
        str(code_dir),
        str(tests_dir)
    ]
    format_success = run_command(format_cmd, "Formatting code with Black")

    # 2. Lint with Ruff
    # Using the version pinned in requirements.txt
    lint_cmd = [
        sys.executable, "-m", "ruff",
        "check",
        "--config", str(project_root / "pyproject.toml"),
        str(code_dir),
        str(tests_dir)
    ]
    lint_success = run_command(lint_cmd, "Linting code with Ruff")

    if not (format_success and lint_success):
        print("One or more checks failed. Please fix the issues above.")
        sys.exit(1)

    print("All linting and formatting checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
