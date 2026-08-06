"""
T002b: Initialize Python 3.11 virtual environment and verify version.

This script creates a virtual environment at `code/venv` using Python 3.11
and verifies that the resulting interpreter reports version 3.11.x.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "code" / "venv"
    
    # Check if venv already exists
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)
    
    # Check for Python 3.11
    python_executable = sys.executable
    version_info = sys.version_info
    
    print(f"Current Python version: {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    if version_info.major != 3 or version_info.minor != 11:
        # Try to find python3.11 explicitly
        try:
            result = subprocess.run(
                ["python3.11", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Found python3.11: {result.stdout.strip()}")
            python_executable = "python3.11"
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: Python 3.11 is required to create the virtual environment.")
            print(f"Current interpreter: {sys.executable} ({version_info.major}.{version_info.minor})")
            print("Please run this script with 'python3.11' or ensure python3.11 is in your PATH.")
            sys.exit(1)
    
    # Create the virtual environment
    print(f"Creating virtual environment at {venv_path} using {python_executable}...")
    try:
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment.")
        print(f"stdout: {e.stdout.decode()}")
        print(f"stderr: {e.stderr.decode()}")
        sys.exit(1)
    
    # Verify the venv python version
    venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        # Fallback for Windows or different structure
        venv_python = venv_path / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print(f"ERROR: Could not find python executable in virtual environment at {venv_python}")
        sys.exit(1)
    
    try:
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_output = result.stdout.strip()
        print(f"Verification: {version_output}")
        
        # Check version format (3.11.x)
        if "3.11" in version_output:
            print("SUCCESS: Virtual environment created and verified as Python 3.11.x.")
            return 0
        else:
            print(f"ERROR: Virtual environment is not Python 3.11.x. Found: {version_output}")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Could not verify virtual environment version.")
        print(f"stderr: {e.stderr.decode()}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())