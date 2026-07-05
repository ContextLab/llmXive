"""
Script to configure and verify linting and formatting tools.
This script ensures that flake8, black, and pre-commit are installed
and configured according to project standards.
"""
import subprocess
import sys
from pathlib import Path

def check_command(command: str) -> bool:
    """Check if a command is available in the system."""
    try:
        subprocess.run(
            ["which", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_packages() -> None:
    """Install required linting and formatting packages."""
    packages = ["flake8", "black", "isort", "pre-commit"]
    for package in packages:
        if not check_command(package):
            print(f"Installing {package}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True
            )
        else:
            print(f"{package} is already installed.")

def run_linter() -> int:
    """Run flake8 on the code directory."""
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            ["flake8", str(code_dir)],
            cwd=code_dir,
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Flake8 check passed: No linting errors found.")
        else:
            print("Flake8 check failed:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Please install it first.")
        return 1

def run_formatter_check() -> int:
    """Run black check on the code directory."""
    code_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            cwd=code_dir,
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Black check passed: Code is formatted correctly.")
        else:
            print("Black check failed:")
            print(result.stdout)
            print("Run 'black code/' to format the code.")
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it first.")
        return 1

def main() -> int:
    """Main entry point for the setup script."""
    print("Setting up linting and formatting tools...")
    install_packages()
    print("\nRunning linter...")
    lint_result = run_linter()
    print("\nRunning formatter check...")
    format_result = run_formatter_check()

    if lint_result == 0 and format_result == 0:
        print("\n✅ All checks passed! Linting and formatting are configured correctly.")
        return 0
    else:
        print("\n⚠️ Some checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())