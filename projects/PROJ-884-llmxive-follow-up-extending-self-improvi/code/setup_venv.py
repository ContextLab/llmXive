import os
import subprocess
import sys
import shutil
from pathlib import Path

def find_python311() -> str:
    """
    Locates the Python 3.11 interpreter.
    Returns the path to the executable.
    Raises FileNotFoundError if not found.
    """
    candidates = [
        "python3.11",
        "python3.11.exe",
        "/usr/bin/python3.11",
        "/usr/local/bin/python3.11",
    ]
    
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            if "3.11" in result.stdout:
                return candidate
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # Fallback: try generic python3 and check version
    try:
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        if "3.11" in result.stdout:
            return "python3"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    raise FileNotFoundError(
        "Python 3.11 interpreter not found. "
        "Please install Python 3.11 and ensure it is in PATH or named 'python3.11'."
    )

def main():
    """
    Initializes a Python 3.11 virtual environment in the project root.
    The project root is determined by the presence of 'tasks.md' or 'plan.md'.
    """
    # Determine project root (current working directory or parent if needed)
    # Assuming this script is run from the project root or code/ subdirectory
    current_path = Path.cwd()
    project_root = current_path
    
    # If running from code/, go up one level
    if project_root.name == "code":
        project_root = project_root.parent

    venv_path = project_root / "venv"
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        print("To recreate, manually remove the directory and re-run this script.")
        return

    print(f"Locating Python 3.11 interpreter...")
    python_exe = find_python311()
    print(f"Found interpreter: {python_exe}")

    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        sys.exit(1)

    # Verify creation
    if not (venv_path / "bin" / "activate").exists() and not (venv_path / "Scripts" / "activate.bat").exists():
        print("Virtual environment creation verification failed.")
        sys.exit(1)

    print("Virtual environment created successfully.")
    print(f"Activate with: source {venv_path / 'bin' / 'activate'} (Unix)")
    print(f"Activate with: {venv_path / 'Scripts' / 'activate.bat'} (Windows)")

if __name__ == "__main__":
    main()
