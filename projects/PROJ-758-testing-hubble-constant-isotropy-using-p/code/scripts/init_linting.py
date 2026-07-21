import os
import subprocess
import sys
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a specific tool is installed and available."""
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

def check_config_files() -> bool:
    """Verify that configuration files exist in the project root."""
    config_files = [
        "pyproject.toml",
    ]
    missing = []
    for cfg in config_files:
        if not Path(cfg).exists():
            missing.append(cfg)
    
    if missing:
        print(f"Missing configuration files: {', '.join(missing)}")
        return False
    return True

def run_lint_check() -> int:
    """Run ruff linting on the codebase."""
    if not check_tool("ruff"):
        print("Error: ruff is not installed. Run: pip install ruff")
        return 1
    
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Linting failed: {e}")
        return 1

def run_format_check() -> int:
    """Run black formatting check on the codebase."""
    if not check_tool("black"):
        print("Error: black is not installed. Run: pip install black")
        return 1
    
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Formatting check failed: {e}")
        return 1

def main():
    """Main entry point for initialization and validation."""
    print("Checking linting and formatting configuration...")
    
    if not check_config_files():
        print("Configuration check failed. Please ensure pyproject.toml exists.")
        sys.exit(1)
    
    print("Configuration files found.")
    
    # Optional: Run checks to verify setup
    # lint_code = run_lint_check()
    # format_code = run_format_check()
    
    # if lint_code != 0:
    #     print("Linting issues found. Run 'ruff check --fix' to fix.")
    # if format_code != 0:
    #     print("Formatting issues found. Run 'black .' to fix.")
    
    print("Linting and formatting configuration is ready.")
    print("To run checks manually:")
    print("  ruff check .")
    print("  black --check .")
    print("To auto-fix:")
    print("  ruff check --fix .")
    print("  black .")

if __name__ == "__main__":
    main()