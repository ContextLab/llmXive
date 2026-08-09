"""
Module to handle the setup and verification of linting and formatting tools.
Implements T003: Configure linting and formatting tools (ruff, black).
"""
import subprocess
import sys
import os
from pathlib import Path
import json

def run_command(cmd: list, capture_output: bool = True) -> tuple:
    """
    Run a shell command and return (return_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_tool_availability(tool_name: str) -> bool:
    """
    Check if a specific tool is installed and available in PATH.
    """
    return_code, _, _ = run_command([tool_name, "--version"])
    return return_code == 0

def check_config_file(config_path: str) -> bool:
    """
    Verify that the configuration file exists and is readable.
    """
    path = Path(config_path)
    return path.exists() and path.is_file()

def run_lint_check() -> tuple:
    """
    Run ruff linting on the codebase.
    Returns (success, message).
    """
    if not check_tool_availability("ruff"):
        return False, "Ruff is not installed. Please install it via 'pip install ruff'."
    
    # Run ruff check on the code directory
    code_dir = Path(__file__).parent
    return_code, stdout, stderr = run_command(["ruff", "check", str(code_dir)])
    
    if return_code == 0:
        return True, "Linting passed successfully."
    else:
        return False, f"Linting failed:\n{stdout}\n{stderr}"

def run_format_check() -> tuple:
    """
    Run black format check on the codebase.
    Returns (success, message).
    """
    if not check_tool_availability("black"):
        return False, "Black is not installed. Please install it via 'pip install black'."
    
    code_dir = Path(__file__).parent
    return_code, stdout, stderr = run_command(["black", "--check", str(code_dir)])
    
    if return_code == 0:
        return True, "Formatting check passed."
    else:
        return False, f"Formatting issues found:\n{stdout}\n{stderr}"

def main():
    """
    Main entry point for the linting setup script.
    Performs checks and reports status.
    """
    print("=== Linting and Formatting Tool Setup Verification ===")
    
    # Check configuration files
    config_files = [
        "pyproject.toml",
        ".ruff.toml",
        ".black.toml"
    ]
    
    missing_configs = []
    for cfg in config_files:
        if not check_config_file(cfg):
            missing_configs.append(cfg)
    
    if missing_configs:
        print(f"WARNING: Missing configuration files: {missing_configs}")
    else:
        print("OK: All configuration files found.")

    # Check tool availability
    tools = ["ruff", "black"]
    installed_tools = []
    missing_tools = []

    for tool in tools:
        if check_tool_availability(tool):
            installed_tools.append(tool)
            print(f"OK: {tool} is installed.")
        else:
            missing_tools.append(tool)
            print(f"MISSING: {tool} is not installed.")

    if missing_tools:
        print(f"\nACTION REQUIRED: Install missing tools: pip install {' '.join(missing_tools)}")
        sys.exit(1)

    # Run checks
    print("\n--- Running Lint Check ---")
    lint_success, lint_msg = run_lint_check()
    print(lint_msg)

    print("\n--- Running Format Check ---")
    fmt_success, fmt_msg = run_format_check()
    print(fmt_msg)

    if lint_success and fmt_success:
        print("\n=== SUCCESS: Linting and formatting tools are configured and passing ===")
        sys.exit(0)
    else:
        print("\n=== WARNING: Issues found in linting or formatting ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
