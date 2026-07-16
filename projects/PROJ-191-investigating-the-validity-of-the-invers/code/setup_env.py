"""
Project initialization script for PROJ-191.
Creates the virtual environment and installs pinned dependencies.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    venv_dir = project_root / ".venv"
    requirements_file = code_dir / "requirements.txt"

    if not requirements_file.exists():
        print(f"Error: requirements.txt not found at {requirements_file}")
        sys.exit(1)

    print(f"Initializing Python environment in {venv_dir}...")

    # Create virtual environment
    if not venv_dir.exists():
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True
        )
        print("Virtual environment created.")
    else:
        print("Virtual environment already exists.")

    # Determine the path to the python executable in the venv
    python_exe = venv_dir / "bin" / "python" if os.name != "nt" else venv_dir / "Scripts" / "python.exe"

    # Upgrade pip
    subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        check=True
    )
    print("Pip upgraded.")

    # Install dependencies
    print(f"Installing dependencies from {requirements_file}...")
    subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)],
        check=True
    )
    print("Dependencies installed successfully.")
    print(f"\nTo activate the environment, run:")
    if os.name == "nt":
        print(f"  {venv_dir}\\Scripts\\activate")
    else:
        print(f"  source {venv_dir}/bin/activate")

if __name__ == "__main__":
    main()