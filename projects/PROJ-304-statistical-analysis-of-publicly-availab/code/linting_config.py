"""
Configuration utilities for linting and formatting tools.
"""
import os
import subprocess
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_ruff_config() -> bool:
    """Ensure ruff configuration exists in pyproject.toml."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"
    
    if not pyproject.exists():
        print("Error: pyproject.toml not found")
        return False
    
    with open(pyproject, 'r') as f:
        content = f.read()
    
    if "[tool.ruff]" not in content:
        print("Warning: [tool.ruff] section not found in pyproject.toml")
        return False
    
    return True

def ensure_black_config() -> bool:
    """Ensure black configuration exists in pyproject.toml."""
    project_root = get_project_root()
    pyproject = project_root / "pyproject.toml"
    
    if not pyproject.exists():
        print("Error: pyproject.toml not found")
        return False
    
    with open(pyproject, 'r') as f:
        content = f.read()
    
    if "[tool.black]" not in content:
        print("Warning: [tool.black] section not found in pyproject.toml")
        return False
    
    return True

def check_tools_installed() -> bool:
    """Check if required tools (ruff, black) are installed."""
    tools = ["ruff", "black"]
    missing = []
    
    for tool in tools:
        try:
            subprocess.run(
                [tool, "--version"],
                check=True,
                capture_output=True,
                text=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
    
    if missing:
        print(f"Error: Missing required tools: {', '.join(missing)}")
        print("Install them with: pip install ruff black")
        return False
    
    return True

def run_lint_check() -> bool:
    """Run ruff lint check."""
    try:
        subprocess.run(
            ["ruff", "check", "."],
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def run_format_check() -> bool:
    """Run black format check."""
    try:
        subprocess.run(
            ["black", "--check", "."],
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def initialize_config():
    """Initialize linting and formatting configuration."""
    print("Checking linting configuration...")
    
    if not check_tools_installed():
        return False
    
    if not ensure_ruff_config():
        print("Ruff configuration check failed.")
        return False
    
    if not ensure_black_config():
        print("Black configuration check failed.")
        return False
    
    print("Configuration validated successfully.")
    return True
