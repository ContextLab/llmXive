import subprocess
import sys
import os
from pathlib import Path

def setup_virtualenv_and_install():
    """
    Creates a virtual environment in 'venv' at the project root
    and installs dependencies from 'requirements.txt'.
    """
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {requirements_path}")

    print(f"Creating virtual environment at {venv_path}...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    venv_python = venv_path / "bin" / "python" if os.name != "nt" else venv_path / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        raise RuntimeError(f"Virtual environment python not found at {venv_python}")

    print("Upgrading pip...")
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)

    print("Installing dependencies from requirements.txt...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)],
        check=True
    )

    print("Virtual environment setup and dependency installation complete.")

if __name__ == "__main__":
    setup_virtualenv_and_install()