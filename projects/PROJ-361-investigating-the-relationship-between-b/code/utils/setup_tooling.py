"""
Utility module to initialize and run project tooling (linting, formatting, type checking).
"""
import subprocess
import sys
import os


def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and report success/failure.

    Args:
        cmd: List of command arguments.
        description: Human-readable description of the action.

    Returns:
        True if the command succeeded, False otherwise.
    """
    print(f"Running: {description}...")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {description} failed with exit code {e.returncode}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Ensure tools are installed: {cmd[0]}")
        return False


def main() -> int:
    """
    Main entry point for running linting, formatting, and type checking.
    """
    print("=== Project Tooling Runner ===")

    # 1. Format with Black
    success = run_command(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        "Black formatting check",
    )
    if not success:
        print("Formatting check failed. Run 'black code/ tests/' to fix.")
        return 1

    # 2. Lint with Flake8
    success = run_command(
        [sys.executable, "-m", "flake8", "code/", "tests/"],
        "Flake8 linting check",
    )
    if not success:
        print("Linting check failed. Run 'flake8 code/ tests/' to fix.")
        return 1

    # 3. Type check with Mypy
    success = run_command(
        [sys.executable, "-m", "mypy", "code/", "tests/"],
        "Mypy type checking",
    )
    if not success:
        print("Type checking failed. Run 'mypy code/ tests/' to fix.")
        return 1

    print("=== All tooling checks passed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
