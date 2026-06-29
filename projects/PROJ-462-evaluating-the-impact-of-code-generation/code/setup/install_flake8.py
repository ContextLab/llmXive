"""
Install flake8 linter in development environment.

This script installs flake8 in the project's virtual environment
for code linting and style checking.
"""
import os
import subprocess
import sys
from pathlib import Path


def get_venv_paths():
    """Get the paths for the virtual environment."""
    project_root = Path(__file__).parent.parent.parent
    venv_path = project_root / "venv"

    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:
        python_executable = venv_path / "bin" / "python"
        pip_executable = venv_path / "bin" / "pip"

    return python_executable, pip_executable


def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    project_root = Path(__file__).parent.parent.parent
    venv_path = project_root / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return True

    print(f"Creating virtual environment at {venv_path}...")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to create virtual environment: {result.stderr}")
        return False

    print("Virtual environment created successfully.")
    return True


def install_flake8():
    """Install flake8 in the virtual environment."""
    python_executable, pip_executable = get_venv_paths()

    if not pip_executable.exists():
        print(f"Pip executable not found at {pip_executable}")
        return False

    print("Installing flake8...")
    result = subprocess.run(
        [str(pip_executable), "install", "flake8>=6.0.0"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to install flake8: {result.stderr}")
        return False

    print("flake8 installed successfully.")
    return True


def verify_installation():
    """Verify that flake8 is installed and working."""
    python_executable, _ = get_venv_paths()

    if not python_executable.exists():
        print(f"Python executable not found at {python_executable}")
        return False

    print("Verifying flake8 installation...")
    result = subprocess.run(
        [str(python_executable), "-m", "flake8", "--version"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Failed to verify flake8: {result.stderr}")
        return False

    print(f"flake8 version: {result.stdout.strip()}")
    return True


def main():
    """Main entry point for the flake8 installation script."""
    print("=" * 60)
    print("Installing flake8 linter in development environment")
    print("=" * 60)

    # Step 1: Create virtual environment if needed
    if not create_virtual_environment():
        print("ERROR: Failed to create virtual environment.")
        sys.exit(1)

    # Step 2: Install flake8
    if not install_flake8():
        print("ERROR: Failed to install flake8.")
        sys.exit(1)

    # Step 3: Verify installation
    if not verify_installation():
        print("ERROR: Failed to verify flake8 installation.")
        sys.exit(1)

    print("=" * 60)
    print("SUCCESS: flake8 linter installed and verified.")
    print("=" * 60)


if __name__ == "__main__":
    main()