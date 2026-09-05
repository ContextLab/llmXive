"""
Tool to run Ruff (linting) and Black (formatting) on the project.
This script ensures the codebase adheres to the configured standards.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    """Execute a command and raise an error if it fails."""
    print(f"Running: {description}...")
    try:
        result = subprocess.run(
            cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"Success: {description}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing {description}:")
        print(e.stderr)
        raise SystemExit(1) from e


def main() -> None:
    """Main entry point for linting and formatting."""
    project_root = Path(__file__).resolve().parents[1]
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print(f"Project root: {project_root}")

    # 1. Run Black (formatting)
    # We format in-place.
    run_command(
        [sys.executable, "-m", "black", str(code_dir), str(tests_dir)],
        "Black formatting",
    )

    # 2. Run Ruff (linting)
    # We use 'check' to verify without auto-fixing, unless --fix is desired.
    # For CI/automation, we might want to fail on errors.
    run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir), str(tests_dir)],
        "Ruff linting",
    )

    print("All linting and formatting checks passed.")


if __name__ == "__main__":
    main()
