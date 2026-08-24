"""
Setup virtual environment for the project.
This script creates a Python 3.11 virtual environment and installs dependencies.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def find_python311():
    """Find Python 3.11 interpreter."""
    candidates = [
        "python3.11",
        "python3.11",
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
    
    # Fallback to checking python3
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
    
    raise RuntimeError(
        "Python 3.11 not found. Please install Python 3.11 and ensure it is in PATH."
    )

def create_virtual_environment(project_path: Path, venv_name: str = "venv"):
    """Create a virtual environment in the project directory."""
    venv_path = project_path / venv_name
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)
    
    python_exe = find_python311()
    print(f"Creating virtual environment with {python_exe}...")
    
    result = subprocess.run(
        [python_exe, "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to create virtual environment: {result.stderr}"
        )
    
    # Verify the venv was created
    if not (venv_path / "bin" / "activate").exists():
        raise RuntimeError(
            f"Virtual environment created but activation script not found at {venv_path}/bin/activate"
        )
    
    print(f"Virtual environment created successfully at {venv_path}")
    return venv_path

def install_dependencies(venv_path: Path, requirements_path: Path):
    """Install dependencies from requirements.txt into the virtual environment."""
    if not requirements_path.exists():
        print(f"Warning: requirements.txt not found at {requirements_path}. Skipping dependency installation.")
        return
    
    venv_python = venv_path / "bin" / "python"
    venv_pip = venv_path / "bin" / "pip"
    
    # Upgrade pip first
    print("Upgrading pip...")
    result = subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Warning: Failed to upgrade pip: {result.stderr}")
    
    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    result = subprocess.run(
        [str(venv_pip), "install", "-r", str(requirements_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to install dependencies: {result.stderr}"
        )
    
    print("Dependencies installed successfully.")

def main():
    """Main entry point for setting up the virtual environment."""
    # Determine project path
    # The task specifies: projects/PROJ-llmxive-follow-up-extending-self-improvi/
    # We assume this is relative to the repo root
    project_path = Path(__file__).parent.parent / "projects" / "PROJ-884-llmxive-follow-up-extending-self-improvi"
    
    # Create project directory if it doesn't exist
    project_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Setting up virtual environment in {project_path}")
    
    # Create virtual environment
    venv_path = create_virtual_environment(project_path)
    
    # Install dependencies if requirements.txt exists
    requirements_path = project_path.parent / "requirements.txt"
    if requirements_path.exists():
        install_dependencies(venv_path, requirements_path)
    else:
        # Try to find requirements.txt in the repo root
        repo_root = project_path.parent.parent
        requirements_path = repo_root / "requirements.txt"
        if requirements_path.exists():
            install_dependencies(venv_path, requirements_path)
        else:
            print("No requirements.txt found. Skipping dependency installation.")
    
    print("\nVirtual environment setup complete!")
    print(f"To activate, run: source {venv_path}/bin/activate")
    print(f"Then install any additional dependencies with: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
