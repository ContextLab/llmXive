"""
Setup script to install and configure linting and formatting tools.
Installs flake8, pylint, black, and isort, then generates configuration files.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run a shell command and print status."""
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    return result

def install_tools():
    """Install linting and formatting tools via pip."""
    tools = [
        "flake8",
        "pylint",
        "black",
        "isort",
        "tomlkit",  # Required for config generation
        "tomli_w"   # Required for config generation
    ]
    print("Installing linting and formatting tools...")
    for tool in tools:
        print(f"Installing {tool}...")
        run_command([sys.executable, "-m", "pip", "install", tool])
    print("All tools installed successfully.")

def verify_tools():
    """Verify that all tools are installed and accessible."""
    tools = ["flake8", "pylint", "black", "isort"]
    print("Verifying tool installation...")
    for tool in tools:
        try:
            run_command([tool, "--version"], description=f"Checking {tool}")
        except subprocess.CalledProcessError:
            print(f"ERROR: {tool} is not installed or not in PATH.")
            sys.exit(1)
    print("All tools verified.")

def main():
    """Main entry point for setup_linting."""
    print("=" * 60)
    print("Setting up Linting and Formatting Infrastructure")
    print("=" * 60)

    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    print(f"Project root: {project_root}")

    # Install tools
    install_tools()

    # Verify installation
    verify_tools()

    # Generate configuration files
    from lint_config import generate_ruff_toml, generate_pyproject_toml

    print("\nGenerating configuration files...")
    generate_ruff_toml()
    generate_pyproject_toml()
    print("Configuration files generated.")

    print("\n" + "=" * 60)
    print("Linting and Formatting Setup Complete")
    print("=" * 60)
    print("To run linters and formatters manually:")
    print("  flake8 code/ tests/")
    print("  pylint code/ tests/")
    print("  black code/ tests/")
    print("  isort code/ tests/")

if __name__ == "__main__":
    main()
