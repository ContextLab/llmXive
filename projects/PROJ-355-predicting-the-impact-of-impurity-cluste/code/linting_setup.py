import subprocess
import sys
from pathlib import Path

from config import get_project_root

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run(
            [tool_name, "--version"], 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str):
    """Install a tool using pip."""
    print(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        print(f"✓ {tool_name} installed successfully.")
    except subprocess.CalledProcessError:
        print(f"✗ Failed to install {tool_name}.")
        raise

def main():
    """Main entry point for tool installation."""
    root = get_project_root()
    print(f"Checking linting tools in environment for: {root}")
    
    tools = ["ruff", "black"]
    all_installed = True
    
    for tool in tools:
        if not check_tool(tool):
            install_tool(tool)
        else:
            print(f"✓ {tool} is already installed.")
    
    print("\nLinting tool setup complete.")

if __name__ == "__main__":
    main()
