"""
Setup script to verify and initialize linting and formatting tools.
This script checks for the presence of ruff and black, installs them if missing,
and validates the configuration.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            shell=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"

def ensure_tool_installed(tool_name: str) -> bool:
    """Ensure a tool is installed via pip."""
    print(f"Checking for {tool_name}...")
    rc, stdout, stderr = run_command([sys.executable, "-m", "pip", "show", tool_name])
    if rc == 0:
        print(f"  {tool_name} is already installed.")
        return True

    print(f"  Installing {tool_name}...")
    rc, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", tool_name])
    if rc == 0:
        print(f"  Successfully installed {tool_name}.")
        return True
    else:
        print(f"  Failed to install {tool_name}: {stderr}")
        return False

def validate_config() -> bool:
    """Validate the project's linting configuration."""
    print("Validating configuration files...")
    
    # Check pyproject.toml existence
    if not Path("pyproject.toml").exists():
        print("  ERROR: pyproject.toml not found in project root.")
        return False
    
    # Run ruff check (dry run)
    print("  Running ruff check...")
    rc, stdout, stderr = run_command([sys.executable, "-m", "ruff", "check", "."])
    if rc == 0:
        print("    Ruff check passed (no errors found).")
    else:
        # It's okay if there are linting errors in existing code, 
        # as long as the tool runs. We just want to ensure it's configured.
        if "No errors found" in stdout or "Found" in stdout:
            print(f"    Ruff check completed. Output: {stdout[:200]}")
        else:
            print(f"    Ruff check output: {stdout[:200]}")

    # Run black check (dry run)
    print("  Running black check...")
    rc, stdout, stderr = run_command([sys.executable, "-m", "black", "--check", "."])
    if rc == 0:
        print("    Black check passed (all files formatted).")
    else:
        # Again, formatting errors in existing code are expected if not formatted yet.
        if "would reformat" in stdout:
            print("    Black check: Some files need reformatting (expected in new projects).")
        else:
            print(f"    Black check output: {stdout[:200]}")

    return True

def main():
    """Main entry point for setup."""
    print("=== Linting and Formatting Setup ===")
    
    # Ensure tools are available
    tools = ["ruff", "black"]
    success = True
    for tool in tools:
        if not ensure_tool_installed(tool):
            success = False
    
    if not success:
        print("Failed to install required tools.")
        sys.exit(1)

    # Validate configuration
    if not validate_config():
        print("Configuration validation failed.")
        sys.exit(1)

    print("=== Setup Complete ===")
    print("You can now run:")
    print("  - Ruff: python -m ruff check .")
    print("  - Ruff Fix: python -m ruff check . --fix")
    print("  - Black: python -m black .")
    print("  - Black Check: python -m black --check .")

if __name__ == "__main__":
    main()