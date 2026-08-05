import os
import sys
import subprocess
from pathlib import Path

def check_command(cmd: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_if_missing(packages: list[str]) -> None:
    """Install missing packages via pip if they are not found."""
    missing = []
    for pkg in packages:
        # Simple check: try to import
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    else:
        print("All required packages are already installed.")

def main() -> None:
    """Main entry point to setup linting and formatting tools."""
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    # Ensure configuration files exist
    config_files = [
        "pyproject.toml",
        ".ruff.toml",
        ".pre-commit-config.yaml"
    ]

    for f in config_files:
        if not (project_root / f).exists():
            print(f"Warning: Configuration file {f} not found in project root.")
            print("Please ensure T003 artifacts are committed.")

    # Install Python dependencies
    install_if_missing(["ruff", "black", "pre-commit"])

    # Initialize pre-commit hooks
    print("Installing pre-commit hooks...")
    try:
        subprocess.run(["pre-commit", "install"], check=True, cwd=project_root)
        print("Pre-commit hooks installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install pre-commit hooks: {e}")
        sys.exit(1)

    print("Linting and formatting tools configured.")

if __name__ == "__main__":
    main()
