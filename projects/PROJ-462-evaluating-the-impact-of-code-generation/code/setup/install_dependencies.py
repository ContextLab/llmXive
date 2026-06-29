#!/usr/bin/env python3
"""
Task T002b: Install dependencies using pip install -r code/requirements.txt in virtualenv

This script creates a virtual environment and installs all dependencies from
code/requirements.txt.
"""

import os
import subprocess
import sys
from pathlib import Path


def get_venv_paths(venv_path: Path) -> tuple:
    """Return the paths to activate script and pip executable based on OS."""
    if os.name == "nt":  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    return activate_script, pip_path


def create_virtual_environment(venv_path: Path) -> bool:
    """Create a virtual environment at the specified path."""
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return True
    
    print(f"Creating virtual environment at {venv_path}...")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error creating virtual environment: {result.stderr}")
        return False
    
    print("Virtual environment created successfully.")
    return True


def install_dependencies(venv_path: Path, requirements_file: Path) -> bool:
    """Install dependencies from requirements file into the virtual environment."""
    if not requirements_file.exists():
        print(f"Requirements file not found: {requirements_file}")
        return False
    
    # Get the pip executable path
    _, pip_path = get_venv_paths(venv_path)
    
    if not pip_path.exists():
        print(f"pip not found at {pip_path}")
        return False
    
    print(f"Installing dependencies from {requirements_file}...")
    result = subprocess.run(
        [str(pip_path), "install", "-r", str(requirements_file)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error installing dependencies: {result.stderr}")
        print(f"stdout: {result.stdout}")
        return False
    
    print("Dependencies installed successfully.")
    return True


def verify_installation(venv_path: Path) -> bool:
    """Verify that key dependencies were installed correctly."""
    _, pip_path = get_venv_paths(venv_path)
    
    if not pip_path.exists():
        print(f"pip not found at {pip_path}")
        return False
    
    print("Verifying installation...")
    result = subprocess.run(
        [str(pip_path), "list"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running pip list: {result.stderr}")
        return False
    
    # Check for key dependencies
    installed_packages = result.stdout.lower()
    required_packages = ["pandas", "numpy", "scipy", "scikit-learn", "matplotlib", "pyyaml", "requests"]
    
    missing = []
    for pkg in required_packages:
        if pkg not in installed_packages:
            missing.append(pkg)
    
    if missing:
        print(f"Warning: Some packages may not be installed: {missing}")
        return False
    
    print("All required packages verified.")
    return True


def main():
    """Main entry point for the dependency installation script."""
    # Determine paths relative to this script's location
    script_dir = Path(__file__).parent
    code_dir = script_dir.parent  # code/
    project_root = code_dir.parent  # repository root
    
    venv_path = code_dir / "venv"
    requirements_file = code_dir / "requirements.txt"
    
    # Verify requirements file exists
    if not requirements_file.exists():
        print(f"Requirements file not found at {requirements_file}")
        sys.exit(1)
    
    print(f"Project root: {project_root}")
    print(f"Code directory: {code_dir}")
    print(f"Virtual environment path: {venv_path}")
    print(f"Requirements file: {requirements_file}")
    print("-" * 50)
    
    # Create virtual environment if it doesn't exist
    if not create_virtual_environment(venv_path):
        print("Failed to create virtual environment.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies(venv_path, requirements_file):
        print("Failed to install dependencies.")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation(venv_path):
        print("Warning: Could not verify all packages.")
    
    print("-" * 50)
    print("✓ Dependencies installed successfully!")
    print(f"Virtual environment location: {venv_path}")
    
    # Provide activation instructions
    activate_script, _ = get_venv_paths(venv_path)
    if os.name == "nt":
        print(f"Activate with: {activate_script}")
    else:
        print(f"Activate with: source {activate_script}")

if __name__ == "__main__":
    main()
