"""
Script to verify linting and formatting tools are installed and configured.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and returns version info."""
    try:
        if tool_name == "black":
            result = subprocess.run(
                [sys.executable, "-m", "black", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"✓ Black: {result.stdout.strip()}")
            return True
        elif tool_name == "ruff":
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"✓ Ruff: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠ Unknown tool: {tool_name}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ {tool_name} not found or failed: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ {tool_name} not found in PATH")
        return False

def run_check_format(project_root: Path) -> bool:
    """Run black check on the project."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print("⚠ Code directory not found, skipping format check.")
        return True

    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print("✓ Code formatting check passed (black).")
            return True
        else:
            print("✗ Code formatting check failed (black).")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error running black check: {e}")
        return False

def run_check_lint(project_root: Path) -> bool:
    """Run ruff check on the project."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print("⚠ Code directory not found, skipping lint check.")
        return True

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print("✓ Linting check passed (ruff).")
            return True
        else:
            print("✗ Linting check failed (ruff).")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error running ruff check: {e}")
        return False

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    print(f"Project root: {project_root}")

    print("\n--- Checking Tool Installation ---")
    tools_ok = True
    for tool in ["black", "ruff"]:
        if not check_tool(tool):
            tools_ok = False

    if not tools_ok:
        print("\n⚠ Some tools are missing. Install them via:")
        print("  pip install -r requirements-dev.txt")
        sys.exit(1)

    print("\n--- Running Checks ---")
    format_ok = run_check_format(project_root)
    lint_ok = run_check_lint(project_root)

    if format_ok and lint_ok:
        print("\n✓ All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\n✗ Some checks failed. Please fix the issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()