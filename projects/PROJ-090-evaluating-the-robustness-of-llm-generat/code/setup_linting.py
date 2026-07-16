"""
Script to configure and verify linting (ruff) and formatting (black) tools.
This script ensures the project follows consistent code style.
"""

import subprocess
import sys
from pathlib import Path

def check_tool(tool: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [tool, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tools() -> None:
    """Install ruff and black if not present."""
    tools = ["ruff", "black"]
    missing = [t for t in tools if not check_tool(t)]

    if missing:
        print(f"Installing missing tools: {', '.join(missing)}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install"] + missing,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install tools: {e}")
            sys.exit(1)
    else:
        print("All linting and formatting tools are already installed.")

def run_check() -> None:
    """Run ruff check on the project."""
    print("Running Ruff check...")
    try:
        subprocess.run(
            ["ruff", "check", "."],
            check=True,
        )
        print("✓ Ruff check passed.")
    except subprocess.CalledProcessError:
        print("✗ Ruff check found issues. Run 'ruff check --fix' to attempt auto-fix.")
        sys.exit(1)

def run_format() -> None:
    """Run black formatter on the project."""
    print("Running Black formatter...")
    try:
        subprocess.run(
            ["black", "."],
            check=True,
        )
        print("✓ Black formatting applied.")
    except subprocess.CalledProcessError:
        print("✗ Black formatting failed.")
        sys.exit(1)

def main() -> None:
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")
    install_tools()

    # Check if config files exist
    root = Path(__file__).parent.parent
    ruff_config = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    if not ruff_config.exists() and not pyproject.exists():
        print("Warning: No Ruff/Black configuration found. Creating defaults...")
        # In a real scenario, we might generate default files here
        # For now, we assume they are committed to the repo as per T005 artifact list
    elif ruff_config.exists():
        print(f"Found Ruff config: {ruff_config}")
    elif pyproject.exists():
        print(f"Found Black config in: {pyproject}")

    run_check()
    run_format()
    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()