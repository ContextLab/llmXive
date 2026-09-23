"""
Verification script for the Python virtual environment.
This script activates the venv (conceptually, by checking paths),
verifies the Python version, and lists installed packages.
It is designed to be run from the project root or the venv directory.
"""
import os
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    """Determine the project root directory."""
    # The project root is the parent of 'code'
    current = Path(__file__).resolve()
    code_dir = current.parent
    # If this file is in code/setup_venv/, project root is code/..
    if code_dir.name == "code":
        return code_dir.parent
    # Fallback: look for the specific project folder name
    candidate = current.parent.parent.parent.parent
    if candidate.name == "PROJ-871-llmxive-follow-up-extending-planbench-xl":
        return candidate
    return Path.cwd()

def verify_venv() -> bool:
    """
    Verify that the virtual environment is correctly set up.
    Checks:
    1. The venv directory exists.
    2. The Python executable exists and is valid.
    3. The 'python --version' command works.
    4. The 'pip list' command works and shows expected packages.
    """
    project_root = get_project_root()
    venv_path = project_root / "venv"
    python_exec = venv_path / "bin" / "python"
    
    # Check if venv directory exists
    if not venv_path.exists():
        print(f"ERROR: Virtual environment directory not found at {venv_path}")
        return False

    # Check if python executable exists
    if not python_exec.exists():
        print(f"ERROR: Python executable not found at {python_exec}")
        return False

    print(f"Verifying virtual environment at: {venv_path}")
    print("-" * 40)

    # 1. Check Python Version
    try:
        result = subprocess.run(
            [str(python_exec), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Python Version: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to get Python version: {e}")
        return False
    except FileNotFoundError:
        print(f"ERROR: Python executable not found at {python_exec}")
        return False

    # 2. Check Pip List
    try:
        result = subprocess.run(
            [str(python_exec), "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        print("\nInstalled Packages:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors from pip:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run pip list: {e}")
        return False

    print("-" * 40)
    print("Verification successful.")
    return True

def main():
    """Entry point for the verification script."""
    success = verify_venv()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
