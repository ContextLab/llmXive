import subprocess
import sys
import os
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a linting or formatting tool is installed."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> bool:
    """Install a tool via pip if not already installed."""
    print(f"Installing {tool_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", tool_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {tool_name}")
        return False

def run_lint_check(project_root: Path) -> bool:
    """Run ruff or flake8 linting on the code directory."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print(f"Code directory not found: {code_dir}")
        return False

    # Prefer ruff if installed, else flake8
    if check_tool_installed("ruff"):
        cmd = ["ruff", "check", str(code_dir)]
        tool_name = "ruff"
    elif check_tool_installed("flake8"):
        cmd = ["flake8", str(code_dir)]
        tool_name = "flake8"
    else:
        print("No linter (ruff or flake8) found.")
        return False

    print(f"Running {tool_name}...")
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print(f"{tool_name} passed.")
            return True
        else:
            print(f"{tool_name} found issues.")
            return False
    except FileNotFoundError:
        print(f"{tool_name} not found in PATH.")
        return False

def run_format_check(project_root: Path) -> bool:
    """Run black formatting check on the code directory."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print(f"Code directory not found: {code_dir}")
        return False

    if not check_tool_installed("black"):
        print("Black not found. Attempting to install...")
        if not install_tool("black"):
            return False

    cmd = ["black", "--check", "--diff", str(code_dir)]
    print("Running black check...")
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("Black formatting check passed.")
            return True
        else:
            print("Black formatting issues found.")
            return False
    except FileNotFoundError:
        print("Black not found in PATH.")
        return False

def main():
    """Main entry point for linting and formatting setup."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    # Ensure tools are available
    tools = ["ruff", "black"]
    for tool in tools:
        if not check_tool_installed(tool):
            print(f"{tool} is not installed.")
            if not install_tool(tool):
                print(f"Could not install {tool}. Please install manually.")
                sys.exit(1)

    # Run checks
    lint_ok = run_lint_check(project_root)
    format_ok = run_format_check(project_root)

    if lint_ok and format_ok:
        print("\nAll linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\nSome checks failed. Please fix the issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()