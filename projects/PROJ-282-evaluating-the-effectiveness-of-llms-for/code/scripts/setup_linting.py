"""
Script to configure linting (ruff) and formatting (black) tools.
This script ensures the necessary configuration files exist and installs
the tools via pip if they are missing.
"""
import os
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    """Returns the path to the project root (code/ directory)."""
    return Path(__file__).resolve().parent.parent

def check_command(command: str) -> bool:
    """Checks if a command is available in the system PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_if_missing(package: str, command: str) -> None:
    """Installs a package via pip if the corresponding command is missing."""
    if not check_command(command):
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Successfully installed {package}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")
            sys.exit(1)
    else:
        print(f"{package} ({command}) is already installed.")

def validate_config_files(project_root: Path) -> None:
    """Validates that required configuration files exist."""
    required_files = [
        project_root / "pyproject.toml",
        project_root / ".pre-commit-config.yaml",
    ]
    missing_files = [f for f in required_files if not f.exists()]

    if missing_files:
        print(f"Error: Missing configuration files: {missing_files}")
        print("Please ensure pyproject.toml and .pre-commit-config.yaml are present.")
        sys.exit(1)

    print("Configuration files validated successfully.")

def run_precommit_install(project_root: Path) -> None:
    """Installs pre-commit hooks."""
    pre_commit_path = project_root / ".pre-commit-config.yaml"
    if pre_commit_path.exists():
        print("Installing pre-commit hooks...")
        try:
            subprocess.check_call(
                ["pre-commit", "install", "--config", str(pre_commit_path)]
            )
            print("Pre-commit hooks installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install pre-commit hooks: {e}")
            print("You may need to install pre-commit manually: pip install pre-commit")
    else:
        print("No .pre-commit-config.yaml found. Skipping hook installation.")

def main() -> None:
    """Main entry point for the setup script."""
    project_root = get_project_root()
    print(f"Setting up linting and formatting tools in {project_root}...")

    # Install dependencies if missing
    install_if_missing("black", "black")
    install_if_missing("ruff", "ruff")
    install_if_missing("pre-commit", "pre-commit")

    # Validate configuration files
    validate_config_files(project_root)

    # Install pre-commit hooks
    run_precommit_install(project_root)

    print("Linting and formatting setup complete.")
    print("Run 'pre-commit run --all-files' to check code quality.")

if __name__ == "__main__":
    main()