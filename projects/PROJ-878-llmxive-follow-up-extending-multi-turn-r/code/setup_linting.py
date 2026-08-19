"""
Setup script for linting and formatting tools.
Verifies ruff and black are installed and prints their versions.
"""
import subprocess
import sys

def check_tool(tool: str) -> bool:
    """Check if a tool is installed and print version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", tool, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"{tool}: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print(f"Error: {tool} is not installed or not working correctly.")
        return False
    except FileNotFoundError:
        print(f"Error: {tool} command not found.")
        return False

def main():
    print("Checking linting and formatting tools...")
    ruff_ok = check_tool("ruff")
    black_ok = check_tool("black")

    if ruff_ok and black_ok:
        print("\nTools ready. Run 'ruff check code/' and 'black code/' to lint/format.")
        return 0
    else:
        print("\nPlease install missing tools: pip install ruff black")
        return 1

if __name__ == "__main__":
    sys.exit(main())
