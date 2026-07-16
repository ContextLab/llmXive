import subprocess
import sys
import os
from pathlib import Path

def find_python311() -> str:
    """
    Locate the Python 3.11 interpreter.
    Returns the path to the executable or raises FileNotFoundError.
    """
    candidates = [
        "python3.11",
        "python3.11.exe",
        "python3", 
    ]
    
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and "3.11" in result.stdout:
                # Found the correct version, return the command used
                return candidate
        except FileNotFoundError:
            continue
    
    # Fallback: check sys.executable if it's 3.11
    if sys.version_info >= (3, 11) and sys.version_info < (3, 12):
        return sys.executable

    raise FileNotFoundError(
        "Python 3.11 interpreter not found. "
        "Please install Python 3.11 and ensure it is in your PATH."
    )

def create_venv(venv_path: str, python_exe: str) -> None:
    """
    Create a virtual environment at the specified path using the found Python 3.11.
    """
    print(f"Creating virtual environment at {venv_path} using {python_exe}...")
    try:
        subprocess.run(
            [python_exe, "-m", "venv", venv_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create virtual environment: {e.stderr.decode()}")

def install_dependencies(venv_path: str, requirements_path: str) -> None:
    """
    Install dependencies from requirements.txt into the virtual environment.
    """
    # Determine the pip executable based on OS
    pip_exe = "pip" if os.name != "nt" else "pip.exe"
    pip_path = str(Path(venv_path) / "bin" / pip_exe) if os.name != "nt" else str(Path(venv_path) / "Scripts" / pip_exe)
    
    if not os.path.exists(pip_path):
        # Fallback for some venv structures
        pip_path = str(Path(venv_path) / "Scripts" / "pip") if os.name == "nt" else str(Path(venv_path) / "bin" / "pip")

    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [pip_path, "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        subprocess.run(
            [pip_path, "install", "-r", requirements_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install dependencies: {e.stderr.decode()}")

def main():
    """
    Main entry point for setting up the Python 3.11 virtual environment.
    """
    # Project root is assumed to be the directory containing this script's parent or current dir
    # Based on task description, we are in code/, project root is parent
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {requirements_path}")

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
    else:
        python_exe = find_python311()
        create_venv(str(venv_path), python_exe)
    
    install_dependencies(str(venv_path), str(requirements_path))
    print("Setup complete.")

if __name__ == "__main__":
    main()
