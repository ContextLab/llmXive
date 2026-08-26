import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """
    Initialize a Python 3.11 virtual environment at code/venv.
    Verifies that the created environment uses Python 3.11.x.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "code" / "venv"
    python_executable = sys.executable

    # Check if venv already exists
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}.")
        # Verify version if it exists
        bin_dir = "Scripts" if sys.platform == "win32" else "bin"
        python_bin = venv_path / bin_dir / "python"
        if python_bin.exists():
            try:
                result = subprocess.run(
                    [str(python_bin), "--version"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                version_output = result.stdout.strip()
                print(f"Existing venv Python version: {version_output}")
                if "3.11" not in version_output:
                    print(f"WARNING: Existing venv is not Python 3.11 (found: {version_output}). "
                          "Consider deleting and recreating if 3.11 is strictly required.")
                else:
                    print("Verification successful: Existing venv is Python 3.11.x")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Could not verify version of existing venv: {e}")
                return 1
        return 0

    # Ensure we are running with Python 3.11 to create the venv
    # Note: If the host is not 3.11, we try to find python3.11 specifically
    if sys.version_info[:2] != (3, 11):
        print(f"Current interpreter is {sys.version_info.major}.{sys.version_info.minor}. "
              "Attempting to locate python3.11 explicitly...")
        try:
            # Try common python3.11 executable names
            python311_paths = ["python3.11", "python3.11.exe"]
            found_executable = None
            
            for name in python311_paths:
                try:
                    result = subprocess.run(
                        [name, "--version"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if "3.11" in result.stdout:
                        found_executable = name
                        break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if not found_executable:
                print("ERROR: Could not find 'python3.11' executable on PATH. "
                      "Cannot create a Python 3.11 venv.")
                return 1
            
            print(f"Using found executable: {found_executable}")
            create_cmd = [found_executable, "-m", "venv", str(venv_path)]
        except Exception as e:
            print(f"ERROR: Failed to locate python3.11: {e}")
            return 1
    else:
        print(f"Creating venv using current interpreter ({sys.version})")
        create_cmd = [sys.executable, "-m", "venv", str(venv_path)]

    try:
        print(f"Creating virtual environment at {venv_path}...")
        subprocess.run(create_cmd, check=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e}")
        return 1

    # Verify the created venv version
    bin_dir = "Scripts" if sys.platform == "win32" else "bin"
    python_bin = venv_path / bin_dir / "python"
    
    if not python_bin.exists():
        print(f"ERROR: Python executable not found at {python_bin}")
        return 1

    try:
        result = subprocess.run(
            [str(python_bin), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_output = result.stdout.strip()
        print(f"Verification: {version_output}")
        
        if "3.11" not in version_output:
            print(f"ERROR: Created venv is not Python 3.11 (found: {version_output})")
            return 1
        
        print("SUCCESS: Virtual environment initialized and verified as Python 3.11.x.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Could not verify version of created venv: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
