"""
Setup script for linting (ruff) and formatting (black) tools.
This script ensures the tools are installed and can be run against the project.
"""
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], check: bool = True) -> None:
    """Run a shell command."""
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if check:
            sys.exit(1)


def main() -> None:
    """Main entry point for setup_linting."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    # Ensure dev dependencies are installed
    print("\n--- Installing dev dependencies (ruff, black) ---")
    run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])

    # Verify tools are available
    print("\n--- Verifying ruff and black availability ---")
    run_command(["ruff", "--version"])
    run_command(["black", "--version"])

    # Run linter (check only)
    print("\n--- Running ruff (check mode) ---")
    # We run with --exit-zero to avoid failing the setup script if there are lint errors
    # The goal here is to demonstrate the tool works; actual fixing is a separate step.
    run_command(["ruff", "check", str(project_root), "--exit-zero"])

    # Run formatter (check only)
    print("\n--- Running black (check mode) ---")
    run_command(["black", "--check", str(project_root), "--diff"])

    print("\n--- Setup complete. Run 'ruff check .' and 'black .' to fix issues. ---")


if __name__ == "__main__":
    main()
