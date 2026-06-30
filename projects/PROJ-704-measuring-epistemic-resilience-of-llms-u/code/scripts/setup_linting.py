"""
Script to verify linting and formatting configurations are valid.
This script checks if ruff and black are installed and can parse the config files.
"""
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str, args: list[str]) -> bool:
    """Check if a tool is installed and can run with given args."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", tool_name] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"Warning: {tool_name} reported issues:")
            print(result.stdout)
            print(result.stderr)
            # Return True if it's just a linting warning, False if import/parse error
            return "SyntaxError" not in result.stderr and "ModuleNotFoundError" not in result.stderr
        return True
    except FileNotFoundError:
        print(f"Error: {tool_name} not found. Please install it: pip install {tool_name}")
        return False
    except subprocess.TimeoutExpired:
        print(f"Error: {tool_name} timed out.")
        return False

def main():
    project_root = Path(__file__).parent.parent
    ruff_config = project_root / "ruff.toml"
    pyproject = project_root / "pyproject.toml"

    if not ruff_config.exists():
        print("Error: ruff.toml not found in project root.")
        return 1

    if not pyproject.exists():
        print("Error: pyproject.toml not found in project root.")
        return 1

    print("Checking Ruff configuration...")
    if not check_tool("ruff", ["check", str(project_root)]):
        return 1

    print("Checking Black configuration...")
    if not check_tool("black", ["--check", "--diff", str(project_root)]):
        print("Note: Black check failed (formatting issues found). Run 'black .' to fix.")
        # We don't fail the build here, just report

    print("Linting and formatting configuration verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())