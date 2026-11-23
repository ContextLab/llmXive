"""
Setup script for linting (ruff) and formatting (black) tools.

This script verifies that configuration files exist and attempts to
install the tools if they are not present in the environment.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_tools():
    """Install ruff and black if not present."""
    tools = ["ruff", "black"]
    for tool in tools:
        if not check_tool(tool):
            print(f"Installing {tool}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", tool],
                check=True,
            )
        else:
            print(f"{tool} is already installed.")

def check_config_files():
    """Verify configuration files exist in the code directory."""
    code_dir = Path(__file__).parent
    ruff_config = code_dir / ".ruff.toml"
    black_config = code_dir / "pyproject.toml"
    
    if not ruff_config.exists():
        print(f"Error: Ruff config not found at {ruff_config}")
        return False
    if not black_config.exists():
        print(f"Error: Black config not found at {black_config}")
        return False
        
    print("Configuration files found.")
    return True

def main():
    """Main entry point for setup."""
    print("Setting up linting and formatting tools...")
    
    # Install tools if necessary
    install_tools()
    
    # Verify config files
    if not check_config_files():
        print("Configuration check failed. Please ensure .ruff.toml and pyproject.toml exist in the code/ directory.")
        sys.exit(1)
        
    print("Setup complete. Run 'ruff check .' and 'black --check .' to verify formatting.")

if __name__ == "__main__":
    main()
