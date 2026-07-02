import os
import sys
import subprocess
import venv
from pathlib import Path

def check_python_version(min_version: tuple = (3, 11)) -> bool:
    """Check if the current Python version meets the minimum requirement."""
    current_version = sys.version_info[:2]
    if current_version < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]}+ is required. "
              f"Found {sys.version_info.major}.{sys.version_info.minor}.")
        return False
    print(f"Python version check passed: {sys.version_info.major}.{sys.version_info.minor}")
    return True

def create_venv(venv_path: str = ".venv") -> bool:
    """Create a virtual environment if it doesn't exist."""
    venv_dir = Path(venv_path)
    if venv_dir.exists():
        print(f"Virtual environment at {venv_path} already exists. Skipping creation.")
        return True
    
    try:
        print(f"Creating virtual environment at {venv_path}...")
        venv.create(venv_dir, with_pip=True)
        print("Virtual environment created successfully.")
        return True
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        return False

def install_requirements(requirements_path: str = "requirements.txt") -> bool:
    """Install dependencies from requirements.txt."""
    req_file = Path(requirements_path)
    if not req_file.exists():
        print(f"Warning: {requirements_path} not found. Skipping dependency installation.")
        return True
    
    # Determine the correct pip path
    if os.name == 'nt':
        pip_path = req_file.parent / ".venv" / "Scripts" / "pip.exe"
    else:
        pip_path = req_file.parent / ".venv" / "bin" / "pip"
    
    if not pip_path.exists():
        # Fallback to system pip if venv pip not found (though venv should be active)
        pip_cmd = ["pip", "install", "-r", str(req_file)]
    else:
        pip_cmd = [str(pip_path), "install", "-r", str(req_file)]
    
    try:
        print(f"Installing dependencies from {requirements_path}...")
        subprocess.check_call(pip_cmd)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def verify_installation() -> bool:
    """Verify that critical packages are installed."""
    critical_packages = ["numpy", "pandas", "pyyaml"]
    missing = []
    
    for package in critical_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Warning: Missing critical packages: {', '.join(missing)}")
        return False
    
    print("Critical packages verification passed.")
    return True

def main():
    """Main entry point for project setup."""
    print("Starting project setup...")
    
    # 1. Check Python version
    if not check_python_version((3, 11)):
        sys.exit(1)
    
    # 2. Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # 3. Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # 4. Verify installation
    if not verify_installation():
        print("Warning: Some critical packages might be missing.")
    
    print("Project setup completed.")

if __name__ == "__main__":
    main()