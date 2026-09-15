"""
Script to run Black formatting and Flake8 linting on the project.
Usage: python code/scripts/format_and_lint.py [--fix]
"""
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> None:
    """Execute a shell command."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as e:
        if check:
            raise RuntimeError(f"Command failed with exit code {e.returncode}") from e
        print(f"Command failed (expected): {e}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run formatting and linting tools.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run black in fix mode to automatically correct formatting issues."
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    # Run Black
    black_cmd = [sys.executable, "-m", "black", "--config", str(project_root / "pyproject.toml")]
    if args.fix:
        black_cmd.append(str(code_dir))
        black_cmd.append(str(tests_dir))
        print("Formatting code with Black (fix mode)...")
    else:
        black_cmd.extend(["--check", "--diff", str(code_dir), str(tests_dir)])
        print("Checking formatting with Black...")

    run_command(black_cmd, check=True)

    # Run Flake8
    flake8_cmd = [
        sys.executable, "-m", "flake8",
        "--config", str(project_root / ".flake8"),
        str(code_dir), str(tests_dir)
    ]
    print("Linting code with Flake8...")
    run_command(flake8_cmd, check=True)

    print("All checks passed.")

if __name__ == "__main__":
    main()
