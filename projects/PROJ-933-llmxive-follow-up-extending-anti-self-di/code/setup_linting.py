"""
Script to verify and optionally install linting and formatting tools.
This script ensures that ruff, black, isort, and flake8 are available
in the environment.
"""
import subprocess
import sys
from pathlib import Path

TOOLS = {
    "ruff": "ruff",
    "black": "black",
    "isort": "isort",
    "flake8": "flake8",
}

def check_tool(name: str, pip_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", pip_name, "--version"],
            check=True,
            capture_output=True,
        )
        print(f"✓ {name} is installed.")
        return True
    except subprocess.CalledProcessError:
        print(f"✗ {name} is NOT installed.")
        return False

def install_tools():
    """Install missing tools."""
    missing = [k for k, v in TOOLS.items() if not check_tool(k, v)]
    if missing:
        print(f"\nInstalling missing tools: {', '.join(missing)}...")
        packages = [TOOLS[m] for m in missing]
        subprocess.run([sys.executable, "-m", "pip", "install", *packages], check=True)
        print("✓ Installation complete.")
    else:
        print("\nAll linting and formatting tools are already installed.")

def main():
    """Main entry point."""
    print("Checking linting and formatting environment...")
    install_tools()
    
    # Verify configuration files exist
    base = Path(__file__).parent
    config_files = [
        ".ruff.toml",
        "pyproject.toml",
        ".flake8",
    ]
    
    print("\nVerifying configuration files...")
    for f in config_files:
        if (base / f).exists():
            print(f"✓ {f} found.")
        else:
            print(f"✗ {f} NOT found. Please ensure it exists in the project root.")

if __name__ == "__main__":
    main()