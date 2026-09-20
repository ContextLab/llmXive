"""
Quickstart script to verify Ruff and Black installation and run basic checks.
"""
import subprocess
import sys
from pathlib import Path
from config import get_project_root


def run_command(cmd: list[str], description: str) -> bool:
    """
    Run a command and print its output.

    Args:
        cmd: Command and arguments as a list.
        description: Description of the command for logging.

    Returns:
        True if the command succeeded, False otherwise.
    """
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            cwd=get_project_root(),
            capture_output=False,
            text=True,
            check=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}. Please install the tool.")
        return False


def main() -> int:
    """
    Main entry point for the linting quickstart script.
    """
    print("=== Linting and Formatting Quickstart ===")
    print(f"Project Root: {get_project_root()}")
    print()

    # Check Ruff
    if not run_command(["ruff", "--version"], "Checking Ruff version"):
        print("Ruff is not installed or not in PATH.")
        print("Install with: pip install ruff==0.1.0")
        return 1

    # Check Black
    if not run_command(["black", "--version"], "Checking Black version"):
        print("Black is not installed or not in PATH.")
        print("Install with: pip install black==23.10.0")
        return 1

    print("\n--- Running Ruff Check (Dry Run / Check Only) ---")
    # Run ruff check without auto-fixing to see issues
    if not run_command(
        ["ruff", "check", "code/"], "Running Ruff check on code directory"
    ):
        print("Ruff check found issues or failed. Review output above.")
        # We don't return 1 here because we might just have style warnings
        # that the user needs to fix manually.

    print("\n--- Running Black Check (Dry Run) ---")
    # Run black in check mode
    if not run_command(
        ["black", "--check", "code/"], "Running Black check on code directory"
    ):
        print("Black check found formatting issues. Run 'black code/' to fix.")
        # We don't return 1 here because we might just have style warnings
        # that the user needs to fix manually.

    print("\n=== Linting and Formatting Setup Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
