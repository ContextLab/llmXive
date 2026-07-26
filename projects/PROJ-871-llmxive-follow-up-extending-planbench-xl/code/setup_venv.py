"""
Setup script to initialize a Python virtual environment and install dependencies.

This script:
1. Creates a virtual environment in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/venv`.
2. Installs all dependencies from `requirements.txt`.
3. Generates a log file at `data/logs/venv_setup.log` confirming success or failure.
"""
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Determine the project root directory."""
    # The script is expected to run from the project root or be invoked with the correct context.
    # We assume the current working directory is the project root for this task.
    return Path.cwd()

def main():
    project_root = get_project_root()
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"
    log_path = project_root / "data" / "logs" / "venv_setup.log"

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Project Root: {project_root}")
    print(f"Virtual Environment Path: {venv_path}")
    print(f"Requirements File: {requirements_path}")
    print(f"Log File: {log_path}")

    if not requirements_path.exists():
        error_msg = f"ERROR: requirements.txt not found at {requirements_path}"
        print(error_msg)
        with open(log_path, "w") as f:
            f.write(f"{datetime.now().isoformat()} - {error_msg}\n")
        sys.exit(1)

    # Step 1: Create virtual environment
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        import shutil
        shutil.rmtree(venv_path)

    print("Creating virtual environment...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        error_msg = f"ERROR: Failed to create virtual environment: {e.stderr.decode()}"
        print(error_msg)
        with open(log_path, "w") as f:
            f.write(f"{datetime.now().isoformat()} - {error_msg}\n")
        sys.exit(1)

    # Step 2: Determine the Python executable in the venv
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:
        python_executable = venv_path / "bin" / "python"
        pip_executable = venv_path / "bin" / "pip"

    if not python_executable.exists():
        error_msg = f"ERROR: Python executable not found at {python_executable}"
        print(error_msg)
        with open(log_path, "w") as f:
            f.write(f"{datetime.now().isoformat()} - {error_msg}\n")
        sys.exit(1)

    # Step 3: Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        # Non-fatal, but log it
        print(f"WARNING: Failed to upgrade pip: {e.stderr.decode()}")

    # Step 4: Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    try:
        result = subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Dependencies installed successfully.")
        output_log = result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = f"ERROR: Failed to install dependencies: {e.stderr.decode()}"
        print(error_msg)
        with open(log_path, "w") as f:
            f.write(f"{datetime.now().isoformat()} - {error_msg}\n")
        sys.exit(1)

    # Step 5: Write success log
    success_msg = (
        f"{datetime.now().isoformat()} - SUCCESS: Virtual environment created at {venv_path} "
        f"and dependencies installed from {requirements_path}."
    )
    print(success_msg)
    with open(log_path, "w") as f:
        f.write(success_msg + "\n")
        f.write(f"Output from pip install:\n{output_log}\n")

    print("\nSetup complete. To activate the environment, run:")
    if sys.platform == "win32":
        print(f"    {venv_path}\\Scripts\\activate")
    else:
        print(f"    source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()