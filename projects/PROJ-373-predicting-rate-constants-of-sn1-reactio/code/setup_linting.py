"""
Script to verify that linting (ruff/flake8) and formatting (black) tools are configured
and can be executed. This script checks for the presence of configuration files
and attempts to run the tools on the codebase.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def validate_config_files() -> bool:
    """Check that configuration files exist in the project root."""
    root = Path(__file__).parent.parent
    config_files = [
        "pyproject.toml",
        ".flake8",
    ]
    for f in config_files:
        if not (root / f).exists():
            print(f"ERROR: Missing configuration file: {f}")
            return False
    return True

def run_linter() -> bool:
    """Run ruff on the code directory."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/"],
            capture_output=True,
            text=True,
        )
        # ruff returns 0 if no errors, 1 if errors found. We accept both as "runnable".
        if result.returncode not in (0, 1):
            print(f"Ruff execution failed with code {result.returncode}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error running ruff: {e}")
        return False

def run_formatter() -> bool:
    """Run black in check mode on the code directory."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "code/"],
            capture_output=True,
            text=True,
        )
        # black returns 0 if formatted correctly, 1 if not. We accept both as "runnable".
        if result.returncode not in (0, 1):
            print(f"Black execution failed with code {result.returncode}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"Error running black: {e}")
        return False

def main():
    print("Verifying Linting and Formatting Configuration...")
    print("-" * 50)

    if not validate_config_files():
        print("FAILED: Configuration files missing.")
        sys.exit(1)

    print("Configuration files found.")

    tools = [("ruff", check_tool), ("black", check_tool)]
    for name, checker in tools:
        if checker(name):
            print(f"✓ {name} is installed.")
        else:
            print(f"✗ {name} is NOT installed. Please install: pip install {name}")
            sys.exit(1)

    print("Running Ruff...")
    if run_linter():
        print("✓ Ruff executed successfully.")
    else:
        print("✗ Ruff execution failed.")
        sys.exit(1)

    print("Running Black (check mode)...")
    if run_formatter():
        print("✓ Black executed successfully.")
    else:
        print("✗ Black execution failed.")
        sys.exit(1)

    print("-" * 50)
    print("SUCCESS: Linting and formatting tools are configured and runnable.")

if __name__ == "__main__":
    main()