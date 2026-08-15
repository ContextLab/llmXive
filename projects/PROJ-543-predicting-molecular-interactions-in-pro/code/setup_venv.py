import sys
import subprocess
import os
import shutil
from pathlib import Path

def find_python311() -> str:
    """
    Locate a Python 3.11 interpreter.
    Checks common versioned executables and falls back to 'python3.11'.
    Raises FileNotFoundError if not found.
    """
    candidates = [
        "python3.11",
        "python3.11.exe",
        "/usr/bin/python3.11",
        "/usr/local/bin/python3.11",
        "/opt/homebrew/bin/python3.11",
    ]

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            if "3.11" in result.stdout or "3.11" in result.stderr:
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
        if "3.11" in result.stdout or "3.11" in result.stderr:
            return "python3"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    raise FileNotFoundError(
        "Could not find a Python 3.11 interpreter. "
        "Please install Python 3.11 or ensure 'python3.11' is in PATH."
    )

def main():
    """
    Creates a Python 3.11 virtual environment in the 'code/' directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    venv_path = code_dir / "venv"

    # Ensure code directory exists
    code_dir.mkdir(exist_ok=True)

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return

    python_exe = find_python311()
    print(f"Using Python interpreter: {python_exe}")

    try:
        subprocess.run(
            [python_exe, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Successfully created virtual environment at {venv_path}")
        
        # Verify the python binary exists
        if sys.platform == "win32":
            py_bin = venv_path / "Scripts" / "python.exe"
        else:
            py_bin = venv_path / "bin" / "python"
        
        if not py_bin.exists():
            raise RuntimeError(f"Virtual environment created but python binary not found at {py_bin}")
        
        # Verify version
        version_check = subprocess.run(
            [str(py_bin), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Virtual environment Python version: {version_check.stdout.strip()}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create virtual environment: {e.stderr.decode()}") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred while setting up the virtual environment: {e}") from e

if __name__ == "__main__":
    main()