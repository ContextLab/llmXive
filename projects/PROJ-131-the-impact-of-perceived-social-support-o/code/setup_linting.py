"""
Setup Linting Tools.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_tool_installed(tool: str) -> bool:
    try:
        subprocess.run([tool, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool: str):
    print(f"Installing {tool}...")
    subprocess.run([sys.executable, "-m", "pip", "install", tool], check=True)

def verify_config_files():
    # Check for ruff.toml or pyproject.toml
    base = Path(__file__).parent.parent
    if not (base / "pyproject.toml").exists():
        print("Creating pyproject.toml for ruff...")
        (base / "pyproject.toml").write_text("[tool.ruff]\nline-length = 88\n")

def create_ruff_config():
    pass # Handled by pyproject.toml

def create_black_config():
    pass

def main():
    print("Setting up linting...")
    if not check_tool_installed("ruff"):
        install_tool("ruff")
    verify_config_files()
    print("Linting setup complete.")

if __name__ == "__main__":
    main()
