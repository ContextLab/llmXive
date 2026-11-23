import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """
    Creates a Python 3.11 virtual environment in the project root (venv)
    and installs dependencies from requirements.txt.
    """
    project_root = Path(__file__).resolve().parents[2]
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)

    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e.stderr.decode()}")
        sys.exit(1)

    # Determine the path to the python executable inside the venv
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"

    print("Upgrading pip...")
    subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        check=True
    )

    print(f"Installing dependencies from {requirements_path}...")
    subprocess.run(
        [str(pip_exe), "install", "-r", str(requirements_path)],
        check=True
    )

    print("Virtual environment created and dependencies installed successfully.")
    print(f"To activate, run: source {venv_path / 'bin' / 'activate'} (Linux/Mac) or {venv_path / 'Scripts' / 'activate.bat'} (Windows)")

if __name__ == "__main__":
    main()