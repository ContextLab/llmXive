"""
Task T002a: Create Python 3.11 virtual environment in projects/PROJ-543-predicting-molecular-interactions-in-pro/code/

This module locates a Python 3.11 interpreter and creates a virtual environment
at the specified project root. It exits with a clear error if Python 3.11
is not found on the system.
"""
import sys
import subprocess
import os
import shutil
from pathlib import Path

def find_python311() -> str:
    """
    Locate a Python 3.11 interpreter.
    
    Returns the path to the python3.11 executable.
    Raises FileNotFoundError if not found.
    """
    # Common candidates for Python 3.11
    candidates = [
        "python3.11",
        "python3.11.0",
        "python3.11.1",
        "python3.11.2",
        "python3.11.3",
        "python3.11.4",
        "python3.11.5",
        "python3.11.6",
        "python3.11.7",
        "python3.11.8",
        "python3.11.9",
        # Fallbacks
        "python3",
        "python",
    ]

    for candidate in candidates:
        try:
            # Check if the command exists
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            version_output = result.stdout + result.stderr
            
            # Verify it is actually 3.11
            if "3.11" in version_output:
                # Get the full path to the executable
                python_path = shutil.which(candidate)
                if python_path:
                    return python_path
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    # If we get here, we didn't find a working 3.11
    raise FileNotFoundError(
        "Python 3.11 interpreter not found. "
        "Please install Python 3.11 and ensure it is in your PATH, "
        "or explicitly name the binary 'python3.11'."
    )

def main():
    """
    Main entry point for T002a.
    
    Creates a virtual environment in the code/ directory of the project.
    """
    # Determine project root based on the task description
    # The task says: "in projects/PROJ-543-predicting-molecular-interactions-in-pro/code/"
    # Since this script is running from code/, we assume the project root is the parent.
    # However, to be robust, we check the current working directory structure.
    
    cwd = Path.cwd()
    
    # If we are running from code/, parent is project root
    if cwd.name == "code":
        project_root = cwd.parent
    else:
        # Assume we are in the project root
        project_root = cwd
    
    # Verify we are in the correct project
    expected_project_name = "PROJ-543-predicting-molecular-interactions-in-pro"
    if project_root.name != expected_project_name:
        # Check if we are in a subdirectory of the project
        # Look for the project directory in the parent
        potential_project = cwd / "projects" / expected_project_name
        if potential_project.exists():
            project_root = potential_project
        else:
            print(f"Warning: Current directory '{cwd.name}' does not match expected project '{expected_project_name}'.")
            print(f"Attempting to create venv in: {cwd}/venv")
    
    venv_dir = project_root / "code" / "venv"
    
    print(f"Project Root: {project_root}")
    print(f"Virtual Environment Target: {venv_dir}")
    
    # Find Python 3.11
    try:
        python_exe = find_python311()
        print(f"Found Python 3.11 at: {python_exe}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Remove existing venv if present (idempotent)
    if venv_dir.exists():
        print(f"Removing existing virtual environment at {venv_dir}...")
        shutil.rmtree(venv_dir)
    
    # Create the virtual environment
    print("Creating virtual environment...")
    try:
        subprocess.run(
            [python_exe, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}")
        sys.exit(1)
    
    # Verify the venv was created and has the expected python
    venv_python = venv_dir / "bin" / "python"
    if not venv_python.exists():
        # Fallback for Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print(f"ERROR: Virtual environment created but python executable not found at {venv_python}")
        sys.exit(1)
    
    # Verify version
    try:
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_output = result.stdout + result.stderr
        if "3.11" not in version_output:
            print(f"WARNING: Created venv does not seem to use Python 3.11. Output: {version_output}")
        else:
            print(f"SUCCESS: Virtual environment created with Python 3.11.")
            print(f"Path: {venv_dir}")
            print(f"Activate with: source {venv_dir}/bin/activate  (Linux/Mac) or {venv_dir}\\Scripts\\activate (Windows)")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Could not verify virtual environment python version: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()