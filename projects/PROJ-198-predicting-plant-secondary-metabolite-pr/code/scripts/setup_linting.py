"""
Script to verify and install linting/formatting tools (ruff, black).
This script ensures the development environment is ready for code quality checks.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"stderr: {e.stderr}")
        return False

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            capture_output=True,
        )
        print(f"✓ {tool_name} is installed.")
        return True
    except FileNotFoundError:
        print(f"✗ {tool_name} is not installed.")
        return False

def main() -> int:
    """Main entry point for setup script."""
    print("=== Linting & Formatting Setup ===")

    # Check for tools
    tools = ["ruff", "black"]
    missing_tools = [t for t in tools if not check_tool_installed(t)]

    if missing_tools:
        print("\nMissing tools detected. Attempting to install...")
        if not run_command([sys.executable, "-m", "pip", "install", "ruff", "black"]):
            print("Failed to install tools via pip.")
            return 1

        # Re-check
        all_present = all(check_tool_installed(t) for t in tools)
        if not all_present:
            print("Tools still missing after installation attempt.")
            return 1

    print("\n=== Running Initial Checks ===")
    
    # Run ruff check
    if not run_command(["ruff", "check", "code/"]):
        print("Note: Ruff check found issues (expected in initial setup).")
    
    # Run black check
    if not run_command(["black", "--check", "code/"]):
        print("Note: Black check found formatting issues (expected in initial setup).")

    print("\nSetup complete. Tools are available.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
