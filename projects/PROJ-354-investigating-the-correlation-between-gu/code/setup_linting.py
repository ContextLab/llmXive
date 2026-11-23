"""
Setup script for linting and formatting tools (ruff and black).
This script validates the environment and provides helpers to run the tools.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple


def run_command(cmd: List[str], check: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the exit code, stdout, and stderr.
    
    Args:
        cmd: Command and arguments as a list.
        check: If True, raise CalledProcessError on non-zero exit.
        
    Returns:
        Tuple of (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def check_tool_installed(tool_name: str) -> bool:
    """
    Check if a tool is installed and available in PATH.
    
    Args:
        tool_name: Name of the tool (e.g., 'black', 'ruff').
        
    Returns:
        True if the tool is found, False otherwise.
    """
    try:
        subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_dev_dependencies() -> bool:
    """
    Install development dependencies including black and ruff.
    
    Returns:
        True if installation succeeded, False otherwise.
    """
    print("Installing development dependencies...")
    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
    )
    if returncode != 0:
        print(f"Failed to install dependencies: {stderr}")
        return False
    print("Development dependencies installed successfully.")
    return True


def run_black(paths: Optional[List[str]] = None, check_only: bool = False) -> bool:
    """
    Run black formatter on the codebase.
    
    Args:
        paths: List of paths to format. If None, formats the whole project.
        check_only: If True, only check formatting without modifying files.
        
    Returns:
        True if formatting succeeded (or check passed), False otherwise.
    """
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
    
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("code")
        cmd.append("tests")
    
    print(f"Running black: {' '.join(cmd)}")
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
        
    if returncode == 0:
        print("Black formatting check passed.")
        return True
    else:
        print("Black formatting check failed. Run 'black code tests' to fix.")
        return False


def run_ruff(paths: Optional[List[str]] = None, fix: bool = False) -> bool:
    """
    Run ruff linter on the codebase.
    
    Args:
        paths: List of paths to lint. If None, lints the whole project.
        fix: If True, attempt to auto-fix issues.
        
    Returns:
        True if linting succeeded (no issues or all fixed), False otherwise.
    """
    cmd = [sys.executable, "-m", "ruff"]
    if fix:
        cmd.append("--fix")
    else:
        cmd.append("check")
    
    if paths:
        cmd.extend(paths)
    else:
        cmd.append("code")
        cmd.append("tests")
    
    print(f"Running ruff: {' '.join(cmd)}")
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
        
    if returncode == 0:
        print("Ruff linting check passed.")
        return True
    else:
        print("Ruff linting check failed. Run 'ruff check --fix code tests' to fix.")
        return False


def main() -> int:
    """
    Main entry point for the setup_linting script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Setting up linting and formatting tools...")
    
    # Check if tools are installed
    if not check_tool_installed("black"):
        print("Black not found. Attempting to install dev dependencies...")
        if not install_dev_dependencies():
            print("Failed to install dependencies. Please install manually: pip install -e '.[dev]'")
            return 1
    
    if not check_tool_installed("ruff"):
        print("Ruff not found. Attempting to install dev dependencies...")
        if not install_dev_dependencies():
            print("Failed to install dependencies. Please install manually: pip install -e '.[dev]'")
            return 1
    
    print("Tools are installed. Configuration files (.ruff.toml, pyproject.toml) are ready.")
    print("\nTo run formatting:")
    print("  black code tests")
    print("\nTo run linting:")
    print("  ruff check code tests")
    print("\nTo auto-fix issues:")
    print("  ruff check --fix code tests")
    print("  black code tests")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
