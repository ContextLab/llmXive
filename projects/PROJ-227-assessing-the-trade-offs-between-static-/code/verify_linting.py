"""
Verification script for linting and formatting configuration.
Runs black --check and flake8 to ensure the project adheres to the configured standards.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path) -> int:
    """
    Run a command in the specified directory.
    Returns the exit code of the command.
    """
    print(f"Running: {' '.join(cmd)} in {cwd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}. Please ensure it is installed.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """
    Main entry point for linting verification.
    Checks that .flake8 and pyproject.toml exist and run successfully.
    """
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    # Check for .flake8
    flake8_config = project_root / ".flake8"
    if not flake8_config.exists():
        print(f"Error: {flake8_config} not found.", file=sys.stderr)
        return 1
    print(f"Found {flake8_config}")

    # Check for pyproject.toml
    pyproject_config = project_root / "pyproject.toml"
    if not pyproject_config.exists():
        print(f"Error: {pyproject_config} not found.", file=sys.stderr)
        return 1
    print(f"Found {pyproject_config}")

    # Run black --check
    black_exit = run_command(["black", "--check", "."], project_root)
    if black_exit != 0:
        print("Black check failed.", file=sys.stderr)
        # Do not exit immediately, try flake8 as well to report all issues

    # Run flake8
    flake8_exit = run_command(["flake8", "."], project_root)
    if flake8_exit != 0:
        print("Flake8 check failed.", file=sys.stderr)

    if black_exit == 0 and flake8_exit == 0:
        print("All linting and formatting checks passed.")
        return 0
    else:
        print("Linting or formatting checks failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
