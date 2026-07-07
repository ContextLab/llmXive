"""
Script to install and verify linting and formatting tools.
This task (T003) configures flake8/pylint and black/isort.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a shell command and print status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"  ✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed.")
        print(f"  Error: {e.stderr}")
        return False

def install_tools():
    """Install required linting and formatting tools via pip."""
    tools = [
        "black",
        "isort",
        "flake8",
        "pylint",
        "tomli",  # For reading pyproject.toml if needed in CI
    ]
    print("Installing linting and formatting tools...")
    for tool in tools:
        if not run_command(f"pip install {tool}", f"Install {tool}"):
            raise RuntimeError(f"Failed to install {tool}")
    return True

def verify_tools():
    """Verify that installed tools are accessible."""
    tools = ["black", "isort", "flake8", "pylint"]
    print("Verifying tool availability...")
    for tool in tools:
        if not run_command(f"{tool} --version", f"Check {tool} version"):
            raise RuntimeError(f"Tool {tool} is not available after installation.")
    return True

def main():
    """Main entry point for T003."""
    print("--- Task T003: Configure Linting and Formatting ---")
    try:
        install_tools()
        verify_tools()
        print("\n✓ T003 Completed: Tools installed and verified.")
        print("  Next step: Run `black .` and `isort .` to format code,")
        print("  then run `flake8 .` and `pylint code/` for linting.")
    except RuntimeError as e:
        print(f"\n✗ T003 Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
