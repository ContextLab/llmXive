"""
Script to create a virtual environment in code/.venv and install dependencies.
This script handles the setup for T002a (virtualenv) and T002b (requirements).
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    venv_dir = code_dir / ".venv"
    requirements_file = code_dir / "requirements.txt"

    # Ensure code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print(f"Creating virtual environment in {venv_dir}...")
        try:
            # Use the current Python interpreter to create the venv
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e.stderr.decode()}")
            sys.exit(1)
    else:
        print(f"Virtual environment already exists at {venv_dir}.")

    # 2. Install dependencies from requirements.txt if it exists
    if requirements_file.exists():
        print("Installing dependencies from requirements.txt...")
        venv_python = venv_dir / "bin" / "python" if os.name != "nt" else venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "bin" / "pip" if os.name != "nt" else venv_dir / "Scripts" / "pip.exe"

        try:
            # Upgrade pip first
            subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Install requirements
            subprocess.run(
                [str(venv_pip), "install", "-r", str(requirements_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e.stderr.decode()}")
            sys.exit(1)
    else:
        print(f"Warning: {requirements_file} not found. Skipping dependency installation.")

    # 3. Print activation instructions
    print("\nVirtual environment setup complete.")
    print(f"Activate the environment using:")
    if os.name == "nt":
        print(f"  {venv_dir}\\Scripts\\activate.bat")
    else:
        print(f"  source {venv_dir}/bin/activate")

    return 0

if __name__ == "__main__":
    sys.exit(main())