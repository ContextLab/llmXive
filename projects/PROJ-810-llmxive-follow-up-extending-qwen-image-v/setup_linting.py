"""
Setup script for linting and formatting tools.
Configures ruff, black, and flake8 for the project.
"""
import subprocess
import sys
import os
from pathlib import Path


def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_tools() -> None:
    """Install linting and formatting tools if not already installed."""
    tools = ["ruff", "black"]
    for tool in tools:
        if not check_tool_installed(tool):
            print(f"Installing {tool}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
        else:
            print(f"{tool} is already installed.")


def verify_config_files() -> None:
    """Verify that configuration files exist."""
    project_root = Path(__file__).parent
    config_files = [
        project_root / "pyproject.toml",
        project_root / ".ruff.toml",
        project_root / ".flake8",
    ]

    for config_file in config_files:
        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}"
            )
        print(f"Found configuration file: {config_file}")


def run_lint_check() -> int:
    """Run ruff linting on the codebase."""
    print("Running ruff lint check...")
    result = subprocess.run(
        ["ruff", "check", "code/"],
        cwd=Path(__file__).parent,
    )
    return result.returncode


def run_format_check() -> int:
    """Run black format check on the codebase."""
    print("Running black format check...")
    result = subprocess.run(
        ["black", "--check", "code/"],
        cwd=Path(__file__).parent,
    )
    return result.returncode


def main() -> None:
    """Main entry point for setup script."""
    project_root = Path(__file__).parent

    # Install tools if needed
    install_tools()

    # Verify configuration files exist
    verify_config_files()

    # Run lint check
    lint_exit_code = run_lint_check()
    if lint_exit_code != 0:
        print("Lint check failed. Run 'ruff check --fix code/' to fix issues.")
    else:
        print("Lint check passed.")

    # Run format check
    format_exit_code = run_format_check()
    if format_exit_code != 0:
        print(
            "Format check failed. Run 'black code/' to format code according to style."
        )
    else:
        print("Format check passed.")

    # Exit with appropriate code
    if lint_exit_code != 0 or format_exit_code != 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
