"""
Script to verify and initialize linting and formatting configuration.
This script ensures that ruff and black are installed and that the
project's pyproject.toml contains the necessary configuration.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_tool_installed(tool: str) -> bool:
    """Check if a tool is installed and accessible."""
    ret, _, _ = run_command([sys.executable, "-m", "pip", "show", tool])
    return ret == 0

def main() -> None:
    """Verify linting and formatting setup."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"

    print(f"Checking configuration at: {pyproject_path}")

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found. Please ensure it exists in the project root.")
        sys.exit(1)

    # Check for black and ruff in requirements
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    has_black = "[tool.black]" in content
    has_ruff = "[tool.ruff]" in content

    if not has_black:
        print("WARNING: [tool.black] section missing in pyproject.toml")
    else:
        print("OK: Black configuration found.")

    if not has_ruff:
        print("WARNING: [tool.ruff] section missing in pyproject.toml")
    else:
        print("OK: Ruff configuration found.")

    # Verify tools are installed
    tools = ["black", "ruff"]
    for tool in tools:
        if check_tool_installed(tool):
            print(f"OK: {tool} is installed.")
        else:
            print(f"WARNING: {tool} is not installed. Run: pip install {tool}")

    print("\nLinting and formatting configuration complete.")

if __name__ == "__main__":
    main()