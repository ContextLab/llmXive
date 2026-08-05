"""
Script to configure and verify linting (ruff) and formatting (black) tools.
This script checks for the presence of tools, installs them if missing,
and validates the configuration files.
"""
import os
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    """Returns the project root directory (code/)."""
    return Path(__file__).parent.parent.parent

def check_command(cmd: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            [cmd, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_if_missing(cmd: str, package_name: str) -> None:
    """Install a package if the command is not found."""
    if not check_command(cmd):
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"{package_name} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package_name}: {e}")
            sys.exit(1)
    else:
        print(f"{cmd} is already installed.")

def validate_config_files(project_root: Path) -> bool:
    """Validate that configuration files exist and are readable."""
    config_files = [
        project_root / "pyproject.toml",
        project_root / ".ruff.toml",
        project_root / ".pre-commit-config.yaml"
    ]

    all_valid = True
    for config_file in config_files:
        if not config_file.exists():
            print(f"Error: Configuration file not found: {config_file}")
            all_valid = False
        else:
            print(f"Found configuration: {config_file}")

    return all_valid

def run_precommit_install(project_root: Path) -> bool:
    """Install pre-commit hooks."""
    print("Installing pre-commit hooks...")
    try:
        subprocess.run(
            ["pre-commit", "install"],
            cwd=project_root,
            check=True
        )
        print("Pre-commit hooks installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Warning: Could not install pre-commit hooks: {e}")
        print("Run 'pre-commit install' manually if needed.")
        return False

def main() -> int:
    """Main entry point for linting setup."""
    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # Ensure dependencies are installed
    install_if_missing("ruff", "ruff")
    install_if_missing("black", "black")
    install_if_missing("pre-commit", "pre-commit")

    # Validate configuration files
    if not validate_config_files(project_root):
        print("Configuration validation failed.")
        return 1

    # Install pre-commit hooks
    run_precommit_install(project_root)

    print("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())