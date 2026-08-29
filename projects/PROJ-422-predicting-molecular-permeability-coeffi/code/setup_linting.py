import subprocess
import sys
import os
from pathlib import Path

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed and executable."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_check_format() -> int:
    """Run black --check on the project."""
    print("Running Black format check...")
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=False
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Black check failed. Run 'black .' to fix formatting.")
        return e.returncode

def run_check_lint() -> int:
    """Run ruff check on the project."""
    print("Running Ruff lint check...")
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=False
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Ruff check failed. Run 'ruff check --fix' to fix issues.")
        return e.returncode

def main() -> None:
    """Main entry point for setup_linting."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found. Please run the configuration generator first.")
        sys.exit(1)

    if not check_tool("black"):
        print("Error: Black is not installed. Please install it via pip.")
        sys.exit(1)

    if not check_tool("ruff"):
        print("Error: Ruff is not installed. Please install it via pip.")
        sys.exit(1)

    print("All tools installed. Running checks...")
    
    format_exit = run_check_format()
    lint_exit = run_check_lint()

    if format_exit == 0 and lint_exit == 0:
        print("All checks passed successfully.")
        sys.exit(0)
    else:
        print("One or more checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
