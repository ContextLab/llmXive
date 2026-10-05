import os
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assuming the script is run from the project root or code/setup_venv/
    current = Path(__file__).resolve()
    # Navigate up to the project root based on the known structure
    # code/setup_venv/verify_venv.py -> project root is 3 levels up
    return current.parent.parent.parent

def verify_venv() -> bool:
    """
    Verify that the virtual environment is activated and dependencies are installed.
    Runs:
      1. python --version
      2. pip list
    Returns True if successful, False otherwise.
    """
    project_root = get_project_root()
    venv_path = project_root / "venv"

    if not venv_path.exists():
        print(f"ERROR: Virtual environment not found at {venv_path}")
        return False

    # Determine the python executable based on OS
    if sys.platform == "win32":
        python_exec = venv_path / "Scripts" / "python.exe"
        pip_exec = venv_path / "Scripts" / "pip.exe"
    else:
        python_exec = venv_path / "bin" / "python"
        pip_exec = venv_path / "bin" / "pip"

    if not python_exec.exists():
        print(f"ERROR: Python executable not found at {python_exec}")
        return False

    print(f"Verifying virtual environment at: {venv_path}")
    print("-" * 60)

    # 1. Check Python version
    print("Running: python --version")
    try:
        result = subprocess.run(
            [str(python_exec), "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Stderr: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run python --version: {e}")
        return False
    except FileNotFoundError:
        print(f"ERROR: Python executable '{python_exec}' not found.")
        return False

    print("-" * 60)

    # 2. Check pip list
    print("Running: pip list")
    try:
        result = subprocess.run(
            [str(pip_exec), "list"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run pip list: {e}")
        return False
    except FileNotFoundError:
        print(f"ERROR: Pip executable '{pip_exec}' not found.")
        return False

    print("-" * 60)
    print("Verification successful.")
    return True

def main():
    """Entry point for verification script."""
    success = verify_venv()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()