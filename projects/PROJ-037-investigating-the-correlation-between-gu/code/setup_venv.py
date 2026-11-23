import os
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(command: list, cwd: Path = None) -> None:
    """
    Run a shell command and raise an exception if it fails.
    
    Args:
        command: List of command arguments
        cwd: Working directory for the command
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command failed with exit code {e.returncode}.\n"
            f"STDOUT: {e.stdout}\n"
            f"STDERR: {e.stderr}"
        )

def main():
    """
    Create a virtual environment and install requirements.
    
    This script:
    1. Creates a 'venv' directory in the project root
    2. Activates the environment (conceptually) by using the venv's python
    3. Installs dependencies from requirements.txt
    
    Note: This script is designed to be run from the project root.
    """
    # Determine project root (assuming script is in code/ or code/setup_venv.py)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"
    
    # Check if requirements.txt exists
    if not requirements_path.exists():
        raise FileNotFoundError(
            f"requirements.txt not found at {requirements_path}. "
            "Please create it with the required dependencies first."
        )
    
    # Check if venv already exists
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}.")
        print("Skipping creation. You may want to delete it manually and re-run if issues persist.")
    else:
        print(f"Creating virtual environment at {venv_path}...")
        run_command([sys.executable, "-m", "venv", str(venv_path)])
    
    # Determine the python executable inside the venv
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:
        python_executable = venv_path / "bin" / "python"
        pip_executable = venv_path / "bin" / "pip"
    
    if not python_executable.exists():
        raise RuntimeError(
            f"Python executable not found at {python_executable}. "
            "Virtual environment creation may have failed."
        )
    
    # Upgrade pip
    print("Upgrading pip...")
    run_command([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    print(f"Installing requirements from {requirements_path}...")
    run_command([
        str(pip_executable),
        "install",
        "-r",
        str(requirements_path)
    ])
    
    print(f"Virtual environment setup complete at {venv_path}.")
    print("To activate manually, run:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()