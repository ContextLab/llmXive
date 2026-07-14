"""
Setup script to verify linting and formatting tools are available.
This script checks for flake8, black, and isort installation.
"""
import subprocess
import sys

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and executable."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {tool_name} is installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"✗ {tool_name} is NOT installed or not in PATH")
        return False

def main():
    """Verify all required linting tools are present."""
    tools = ["flake8", "black", "isort"]
    all_present = True

    print("Checking linting and formatting tools...")
    print("-" * 40)

    for tool in tools:
        if not check_tool(tool):
            all_present = False

    print("-" * 40)
    if all_present:
        print("✓ All linting tools are ready.")
        print("\nTo run linting:")
        print("  flake8 code/")
        print("\nTo format code:")
        print("  black code/")
        print("  isort code/")
        return 0
    else:
        print("✗ Some tools are missing. Install them with:")
        print("  pip install flake8 black isort")
        return 1

if __name__ == "__main__":
    sys.exit(main())