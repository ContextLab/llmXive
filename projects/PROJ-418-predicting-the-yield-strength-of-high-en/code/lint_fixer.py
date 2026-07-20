import subprocess
import sys
import os


def run_command(command: list, description: str) -> bool:
    """
    Run a shell command and return success status.

    Args:
        command: List of command arguments
        description: Human-readable description of the command

    Returns:
        True if command succeeded, False otherwise
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True, capture_output=False)
        print(f"Success: {description}\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed: {description} (exit code {e.returncode})\n")
        return False


def main() -> None:
    """Main entry point for linting and fixing."""
    root = os.getenv("PROJECT_ROOT", ".")

    # Run ruff check
    ruff_check_success = run_command(
        [sys.executable, "-m", "ruff", "check", root],
        "Ruff check",
    )

    # Run ruff fix (if available)
    if ruff_check_success:
        run_command(
            [sys.executable, "-m", "ruff", "check", "--fix", root],
            "Ruff auto-fix",
        )

    # Run black
    run_command(
        [sys.executable, "-m", "black", root],
        "Black formatting",
    )


if __name__ == "__main__":
    main()
