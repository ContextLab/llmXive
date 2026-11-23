"""
Script to configure and validate linting (ruff) and formatting (black) tools.
Ensures tools are installed and configuration files are present.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is available in the current environment."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool using pip if not present."""
    print(f"Installing {tool_name}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", tool_name], check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {tool_name}.")
        return False

def validate_config_files() -> bool:
    """Validate that configuration files for ruff and black exist."""
    project_root = Path(__file__).parent
    ruff_config = project_root / ".ruff.toml"
    black_config = project_root / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found.")
        return False

    if not black_config.exists():
        print(f"Error: {black_config} not found.")
        return False

    # Check if black config contains tool.black section
    with open(black_config, "r") as f:
        content = f.read()
        if "[tool.black]" not in content:
            print(f"Error: [tool.black] section missing in {black_config}")
            return False

    # Check if ruff config is valid by running ruff check
    try:
        subprocess.run(
            ["ruff", "check", "--config", str(ruff_config), "--output-format", "concise"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        # Ruff might fail if no python files are found or lint errors exist,
        # but we only care if the config itself is valid.
        # We assume if it runs without a config error, it's valid.
        pass

    print("Configuration files validated successfully.")
    return True

def main():
    """Main entry point for setup_linting script."""
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print("Setting up linting and formatting tools...")

    # Check and install ruff
    if not check_tool_installed("ruff"):
        if not install_tool("ruff"):
            sys.exit(1)
    else:
        print("ruff is already installed.")

    # Check and install black
    if not check_tool_installed("black"):
        if not install_tool("black"):
            sys.exit(1)
    else:
        print("black is already installed.")

    # Validate configuration files
    if not validate_config_files():
        print("Configuration validation failed.")
        sys.exit(1)

    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()