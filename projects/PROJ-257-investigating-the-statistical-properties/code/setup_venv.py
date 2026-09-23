import subprocess
import sys
import os
from pathlib import Path

def find_python311() -> str:
    """
    Locates a Python 3.11 executable.
    Returns the path as a string.
    Raises FileNotFoundError if not found.
    """
    # Common candidates for Python 3.11
    candidates = [
        "python3.11",
        "python3.11.0",
        "python3", # Fallback to system default if explicit version not found, but we check version later
    ]

    for candidate in candidates:
        try:
            # Check if the command exists
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            # Verify it is actually 3.11
            version_output = result.stdout.strip()
            if "3.11" in version_output or "3.11" in result.stderr.strip():
                # Resolve the full path
                full_path = subprocess.run(
                    ["which", candidate],
                    capture_output=True,
                    text=True,
                    check=True
                ).stdout.strip()
                return full_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    # If explicit 3.11 not found, try to find any python3 and check version
    # If the system default is not 3.11, we might need to instruct the user
    # For this implementation, we assume 'python3' or 'python' is acceptable if it's 3.11
    # or we raise an error if we can't find 3.11 specifically.
    # Let's try 'python3' specifically.
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

    try:
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        if "3.11" in result.stdout or "3.11" in result.stderr:
            return "python"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    raise FileNotFoundError("Could not find Python 3.11. Please install python3.11 and ensure it is in your PATH.")

def create_venv(venv_path: str, python_exe: str) -> None:
    """
    Creates a virtual environment at venv_path using the specified python_exe.
    """
    venv_dir = Path(venv_path)
    if venv_dir.exists():
        print(f"Virtual environment at {venv_path} already exists. Removing...")
        import shutil
        shutil.rmtree(venv_dir)

    print(f"Creating virtual environment at {venv_path} using {python_exe}...")
    subprocess.run(
        [python_exe, "-m", "venv", venv_path],
        check=True
    )
    print("Virtual environment created successfully.")

def install_dependencies(venv_path: str, requirements_path: str) -> None:
    """
    Installs dependencies from requirements_path into the virtual environment.
    """
    venv_bin = Path(venv_path) / "bin"
    pip_exe = venv_bin / "pip"

    if not pip_exe.exists():
        raise FileNotFoundError(f"pip not found at {pip_exe}. Virtual environment might be corrupted.")

    print(f"Installing dependencies from {requirements_path}...")
    subprocess.run(
        [str(pip_exe), "install", "--upgrade", "pip"],
        check=True
    )
    subprocess.run(
        [str(pip_exe), "install", "-r", requirements_path],
        check=True
    )
    print("Dependencies installed successfully.")

def main():
    """
    Main entry point for T003: Initialize Python virtual environment and install dependencies.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / ".venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: {requirements_path} not found. Please create requirements.txt first.")
        sys.exit(1)

    try:
        python_exe = find_python311()
        print(f"Using Python executable: {python_exe}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    create_venv(str(venv_path), python_exe)
    install_dependencies(str(venv_path), str(requirements_path))

    # Verification step
    print("\n--- Verification ---")
    verify_cmd = [str(venv_path / "bin" / "python"), "--version"]
    result = subprocess.run(verify_cmd, capture_output=True, text=True)
    print(f"Python version: {result.stdout.strip()}")

    list_cmd = [str(venv_path / "bin" / "pip"), "list"]
    result = subprocess.run(list_cmd, capture_output=True, text=True)
    print("Installed packages:")
    print(result.stdout)

    print("T003 completed successfully.")

if __name__ == "__main__":
    main()
