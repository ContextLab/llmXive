"""
Initialization script to verify linting and formatting tools are configured.

This script checks if ruff and black are installed and validates the 
configuration files (.gitignore, ruff.toml, pyproject.toml) exist.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {tool_name} found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"✗ {tool_name} not found. Please install: pip install {tool_name}")
        return False

def check_config_files() -> bool:
    """Verify required configuration files exist."""
    config_files = [
        ".gitignore",
        "ruff.toml",
        "pyproject.toml"
    ]
    
    base_dir = Path(__file__).parent.parent
    all_exist = True
    
    for cfg in config_files:
        path = base_dir / cfg
        if path.exists():
            print(f"✓ {cfg} exists")
        else:
            print(f"✗ {cfg} missing at {path}")
            all_exist = False
    
    return all_exist

def run_lint_check() -> bool:
    """Run ruff check on the code directory."""
    base_dir = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Ruff check passed")
            return True
        else:
            print(f"⚠ Ruff check found issues (not fatal for init):\n{result.stdout}")
            return True  # Don't fail init just for lint warnings
    except FileNotFoundError:
        print("⚠ Ruff not installed, skipping check")
        return False

def run_format_check() -> bool:
    """Run black check on the code directory."""
    base_dir = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Black check passed")
            return True
        else:
            print(f"⚠ Black check found formatting issues (not fatal for init):\n{result.stdout}")
            return True
    except FileNotFoundError:
        print("⚠ Black not installed, skipping check")
        return False

def main():
    print("Initializing linting and formatting infrastructure...")
    print("-" * 50)
    
    # Check tools
    ruff_ok = check_tool("ruff")
    black_ok = check_tool("black")
    
    # Check config
    config_ok = check_config_files()
    
    if not (ruff_ok and black_ok):
        print("\n⚠ Some tools missing. Install requirements from code/requirements.txt")
        return 1
    
    if not config_ok:
        print("\n✗ Configuration files missing.")
        return 1
    
    # Run checks (non-fatal for init)
    print("-" * 50)
    print("Running validation checks...")
    run_lint_check()
    run_format_check()
    
    print("-" * 50)
    print("✓ Linting and formatting infrastructure ready.")
    print("\nUsage:")
    print("  ruff check .       # Check for lint errors")
    print("  ruff format .      # Format code (if configured)")
    print("  black .            # Format code")
    print("  black --check .    # Check formatting without changing")
    return 0

if __name__ == "__main__":
    sys.exit(main())