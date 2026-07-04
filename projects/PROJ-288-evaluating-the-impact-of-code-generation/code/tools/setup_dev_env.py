"""
Tool to set up the development environment including linting and formatting tools.
This ensures ruff and black are installed and ready to use.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Execute a shell command and return success status."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def ensure_package(package_name: str) -> bool:
    """Ensure a package is installed, install if missing."""
    print(f"Checking for {package_name}...")
    try:
        # Check if package is installed
        subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"✓ {package_name} is already installed.")
        return True
    except subprocess.CalledProcessError:
        print(f"Installing {package_name}...")
        return run_command(
            [sys.executable, "-m", "pip", "install", package_name],
            f"Installing {package_name}"
        )

def main():
    """Main entry point for environment setup."""
    project_root = Path(__file__).resolve().parent.parent
    requirements_file = project_root / "requirements.txt"

    print("Setting up development environment...")
    
    # 1. Install core dependencies from requirements.txt
    if requirements_file.exists():
        print("Installing dependencies from requirements.txt...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            "Installing project dependencies"
        ):
            print("Failed to install dependencies. Please check requirements.txt.")
            sys.exit(1)
    else:
        print(f"Warning: {requirements_file} not found. Skipping dependency installation.")

    # 2. Ensure linting and formatting tools are present
    # Note: These should be in requirements.txt, but we double-check here
    tools = ["black", "ruff"]
    for tool in tools:
        if not ensure_package(tool):
            print(f"Failed to ensure {tool} is installed.")
            sys.exit(1)

    print("\nDevelopment environment setup complete.")
    print("You can now run 'python code/tools/lint_and_format.py' to check code quality.")

if __name__ == "__main__":
    main()