"""
Setup script to initialize the Python 3.11 virtual environment and project structure.
This script ensures the environment is correctly configured before running benchmarks.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    """Initialize the project virtual environment."""
    root_dir = Path(__file__).parent
    venv_dir = root_dir / ".venv"

    print(f"Project root: {root_dir}")
    print(f"Checking Python version...")
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ is required. Current version: {sys.version}")
        sys.exit(1)
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - OK")

    if not venv_dir.exists():
        print(f"Creating virtual environment at {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        print("Virtual environment created.")
    else:
        print(f"Virtual environment already exists at {venv_dir}.")

    # Determine the pip executable path based on OS
    if sys.platform == "win32":
        pip_executable = venv_dir / "Scripts" / "pip.exe"
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:
        pip_executable = venv_dir / "bin" / "pip"
        python_executable = venv_dir / "bin" / "python"

    if not pip_executable.exists():
        print(f"ERROR: pip executable not found at {pip_executable}")
        sys.exit(1)

    print("Upgrading pip...")
    subprocess.run([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"], check=True)

    requirements_file = root_dir / "requirements.txt"
    if requirements_file.exists():
        print(f"Installing dependencies from {requirements_file}...")
        subprocess.run([str(pip_executable), "install", "-r", str(requirements_file)], check=True)
    else:
        print("WARNING: requirements.txt not found. Skipping dependency installation.")

    print("\nSetup complete!")
    print(f"Activate the environment and run the benchmark:")
    if sys.platform == "win32":
        print(f"  .venv\\Scripts\\activate")
    else:
        print(f"  source .venv/bin/activate")
    print("  python -m src.benchmark.run_benchmark --help")

if __name__ == "__main__":
    main()
