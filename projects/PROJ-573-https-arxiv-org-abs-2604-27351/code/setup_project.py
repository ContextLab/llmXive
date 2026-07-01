"""
Project initialization script for Python 3.11 environment setup.
Creates virtual environment, installs dependencies, and validates the setup.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    """Initialize the Python 3.11 project environment."""
    project_root = Path(__file__).parent
    venv_dir = project_root / ".venv"
    requirements_file = project_root / "requirements.txt"

    print("=== llmXive Project Initialization ===")
    print(f"Project root: {project_root}")

    # Verify Python version
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required. Current: {sys.version}")
        sys.exit(1)
    print(f"Python version: {sys.version}")

    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    else:
        print(f"Virtual environment already exists at {venv_dir}")

    # Determine the correct pip executable
    if os.name == "nt":
        pip_executable = venv_dir / "Scripts" / "pip"
    else:
        pip_executable = venv_dir / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    subprocess.run([str(pip_executable), "install", "--upgrade", "pip"], check=True)

    # Install dependencies
    if requirements_file.exists():
        print(f"Installing dependencies from {requirements_file}...")
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_file)],
            check=True
        )
    else:
        print("WARNING: requirements.txt not found. Skipping dependency installation.")

    # Verify installation
    print("\nVerifying installation...")
    try:
        import numpy
        import pandas
        import yaml
        print("✓ Core dependencies installed successfully")
    except ImportError as e:
        print(f"ERROR: Failed to import core dependency: {e}")
        sys.exit(1)

    # Create standard directories if they don't exist
    directories = [
        "code/src",
        "code/tests",
        "code/data",
        "code/data/processed",
        "code/state",
        "code/contracts",
        "code/specs",
        "code/figures",
        "code/results",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py in src subdirectories
        if "src" in dir_path:
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    print("\n=== Initialization Complete ===")
    print(f"Activate environment: source {venv_dir / 'bin' / 'activate'}")
    print("Run benchmark: python code/src/benchmark/run_benchmark.py --help")

if __name__ == "__main__":
    main()