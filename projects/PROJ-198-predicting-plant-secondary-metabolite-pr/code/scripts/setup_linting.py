"""
Script to install and configure linting and formatting tools (ruff, black).
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Run a shell command and raise on failure."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

def check_tool_installed(tool: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        subprocess.run([tool, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main() -> None:
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")

    # Check for pip
    if not check_tool_installed("pip"):
        print("Error: pip not found. Please install Python and pip.")
        sys.exit(1)

    # Install dev dependencies
    print("Installing dev dependencies (ruff, black, pytest)...")
    run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])

    # Verify installation
    tools = ["ruff", "black", "pytest"]
    for tool in tools:
        if check_tool_installed(tool):
            print(f"✓ {tool} is installed.")
        else:
            print(f"✗ {tool} installation failed.")
            sys.exit(1)

    # Create .ruff.toml and .black.toml if they don't exist (optional, mostly for IDEs)
    # The primary config is in pyproject.toml.
    print("Linting and formatting setup complete.")
    print("Run 'ruff check .' to lint.")
    print("Run 'black .' to format.")
    print("Run 'pytest' to test.")

if __name__ == "__main__":
    main()
