"""
Setup and configuration script for linting and formatting tools.
This script ensures that flake8, pylint, black, and isort are installed
and provides a verification command to check the configuration.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, check: bool = True) -> None:
    """Run a shell command and print output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check, text=True)
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running command: {e}")
            sys.exit(1)
        else:
            print(f"Command failed (expected): {e}")


def main():
    """Main entry point for setup_linting."""
    project_root = Path(__file__).parent.parent

    print("=== Setting up Linting and Formatting Tools ===")

    # Install tools if not present
    tools = ["black", "flake8", "pylint", "isort"]
    for tool in tools:
        try:
            __import__(tool.replace("-", "_"))
            print(f"[OK] {tool} is already installed.")
        except ImportError:
            print(f"[INFO] Installing {tool}...")
            run_command([sys.executable, "-m", "pip", "install", tool])

    # Verify configuration files exist
    config_files = {
        ".flake8": project_root / "code" / ".flake8",
        "pyproject.toml": project_root / "code" / "pyproject.toml",
    }

    missing = [f for f, p in config_files.items() if not p.exists()]
    if missing:
        print(f"[ERROR] Missing configuration files: {missing}")
        print("Please ensure .flake8 and pyproject.toml exist in the code/ directory.")
        sys.exit(1)

    print("[OK] All configuration files found.")

    # Run a dry-run check on the code directory to ensure tools work
    print("\n=== Verifying Tools ===")
    run_command(["black", "--check", "--diff", "code/"], check=False)
    run_command(["flake8", "code/"], check=False)
    run_command(["pylint", "code/"], check=False)

    print("\n=== Setup Complete ===")
    print("You can now run:")
    print("  black code/          # Format code")
    print("  flake8 code/         # Lint code")
    print("  pylint code/         # Detailed linting")
    print("  isort code/          # Sort imports")


if __name__ == "__main__":
    main()
