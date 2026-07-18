"""
Setup script to initialize linting and formatting tools for the project.
This script verifies that flake8, black, isort, and pre-commit are installed
and provides instructions for running them.
"""
import subprocess
import sys
from pathlib import Path

TOOLS = {
    "flake8": "flake8 --version",
    "black": "black --version",
    "isort": "isort --version",
    "pre-commit": "pre-commit --version",
}

def check_tool(tool_name, command):
    """Check if a tool is installed and print its version."""
    try:
        result = subprocess.run(
            command.split(),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        print(f"✓ {tool_name}: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print(f"✗ {tool_name} is not installed or not in PATH")
        return False

def install_dev_dependencies():
    """Install development dependencies including linting tools."""
    print("\nInstalling development dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✓ Development dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def main():
    """Main entry point for linting setup."""
    print("=== Linting and Formatting Setup ===\n")

    # Check if requirements-dev.txt exists
    if not Path("requirements-dev.txt").exists():
        print("✗ requirements-dev.txt not found. Creating it...")
        with open("requirements-dev.txt", "w") as f:
            f.write(
                """flake8>=6.0
black>=23.0
isort>=5.12
pytest>=7.0
pytest-cov>=4.0
pre-commit>=3.0
"""
            )
        print("✓ Created requirements-dev.txt")

    # Check existing tools
    print("Checking installed tools:")
    installed_count = 0
    for name, cmd in TOOLS.items():
        if check_tool(name, cmd):
            installed_count += 1

    if installed_count < len(TOOLS):
        print(f"\n⚠ {len(TOOLS) - installed_count} tool(s) missing.")
        response = input("Install development dependencies? [y/N]: ").strip().lower()
        if response == "y":
            if install_dev_dependencies():
                print("\nRe-checking tools after installation:")
                for name, cmd in TOOLS.items():
                    check_tool(name, cmd)
        else:
            print("\nSkipping installation. Run 'pip install -r requirements-dev.txt' manually.")
    else:
        print("\n✓ All linting and formatting tools are installed.")

    # Verify configuration files exist
    print("\nVerifying configuration files:")
    config_files = [".flake8", "pyproject.toml", ".pre-commit-config.yaml"]
    for cfg in config_files:
        if Path(cfg).exists():
            print(f"✓ {cfg} exists")
        else:
            print(f"✗ {cfg} missing")

    print("\n=== Setup Complete ===")
    print("\nUsage:")
    print("  Run linter:        flake8 code/ src/ tests/")
    print("  Run formatter:     black code/ src/ tests/")
    print("  Sort imports:      isort code/ src/ tests/")
    print("  Run pre-commit:    pre-commit run --all-files")
    print("  Install hooks:     pre-commit install")

if __name__ == "__main__":
    main()