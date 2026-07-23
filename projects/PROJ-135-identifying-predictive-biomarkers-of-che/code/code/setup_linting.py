import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tools() -> bool:
    """Install ruff and black if not present."""
    print("Checking and installing linting tools...")
    success = True

    if not check_tool_installed("ruff"):
        print("Installing ruff...")
        if not run_command([sys.executable, "-m", "pip", "install", "ruff"], "Install ruff"):
            success = False

    if not check_tool_installed("black"):
        print("Installing black...")
        if not run_command([sys.executable, "-m", "pip", "install", "black"], "Install black"):
            success = False

    return success

def verify_config_files() -> bool:
    """Verify that configuration files exist in the project root."""
    config_file = Path("pyproject.toml")
    if not config_file.exists():
        print(f"Error: {config_file} not found in project root.")
        return False

    # Check for ruff section
    content = config_file.read_text()
    if "[tool.ruff]" not in content:
        print("Error: [tool.ruff] section missing in pyproject.toml")
        return False

    if "[tool.black]" not in content:
        print("Error: [tool.black] section missing in pyproject.toml")
        return False

    print("Configuration files verified.")
    return True

def run_ruff_check() -> bool:
    """Run ruff check on the codebase."""
    return run_command(["ruff", "check", "."], "Running ruff check")

def run_ruff_format() -> bool:
    """Run ruff format on the codebase."""
    return run_command(["ruff", "format", "."], "Running ruff format")

def run_black_check() -> bool:
    """Run black --check on the codebase."""
    return run_command(["black", "--check", "."], "Running black check")

def main() -> int:
    """Main entry point for linting setup."""
    print("=== Linting and Formatting Setup ===")

    # 1. Install tools
    if not install_tools():
        print("Failed to install tools.")
        return 1

    # 2. Verify config
    if not verify_config_files():
        print("Configuration verification failed.")
        return 1

    # 3. Run checks (optional, just to demonstrate they work)
    print("\n--- Running Initial Checks ---")
    # We run check first, then format. If check fails, we might want to fix it.
    # For setup, we just ensure the commands exist and run.
    run_ruff_check()
    run_ruff_format()
    run_black_check()

    print("\n=== Linting Setup Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())