import sys
import subprocess
import os
import shutil
from pathlib import Path

def find_python311() -> str:
    """
    Locate a Python 3.11 executable on the system.
    Returns the path to the executable or raises FileNotFoundError.
    """
    candidates = [
        "python3.11",
        "python3",
        "python",
    ]

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            version_output = result.stdout + result.stderr
            if "3.11" in version_output:
                # Double check the specific path if 'python' was used
                if candidate == "python" or candidate == "python3":
                    full_path = shutil.which(candidate)
                    if full_path:
                        # Verify version again for the full path to be safe
                        check = subprocess.run(
                            [full_path, "--version"],
                            capture_output=True,
                            text=True,
                            check=True,
                            timeout=10
                        )
                        if "3.11" in check.stdout + check.stderr:
                            return full_path
                return shutil.which(candidate)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue

    raise FileNotFoundError(
        "Could not find a Python 3.11 executable. "
        "Please install Python 3.11 and ensure it is in your PATH, "
        "or explicitly set the PATH environment variable."
    )

def main():
    """
    Creates a Python 3.11 virtual environment in the project's code directory.
    """
    # Determine project root based on the task requirement
    # The task specifies the venv should be in projects/PROJ-543-predicting-molecular-interactions-in-pro/code/
    # We assume the script is run from the project root or we construct the path relative to the script's location if needed.
    # However, the task implies the project structure is already set up (T001a).
    
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    code_dir = script_dir # The venv goes inside 'code'

    venv_path = code_dir / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        # Optionally, we could re-create it, but for idempotency we skip unless forced.
        # For this task, we just ensure it exists.
        return

    python_executable = find_python311()
    print(f"Using Python 3.11 executable: {python_executable}")

    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=False # Let user see the venv creation output
        )
        print("Virtual environment created successfully.")
        
        # Verify the environment was created correctly
        if not (venv_path / "bin" / "activate").exists() and not (venv_path / "Scripts" / "activate.bat").exists():
            raise RuntimeError("Virtual environment creation failed: activation script not found.")
        
        print(f"Virtual environment ready at: {venv_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        raise

if __name__ == "__main__":
    main()
