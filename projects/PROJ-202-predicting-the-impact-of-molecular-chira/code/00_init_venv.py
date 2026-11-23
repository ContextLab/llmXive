import os
import subprocess
import sys
import venv
from pathlib import Path

def check_python_version():
    """Verify Python version is 3.11."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"Error: Python 3.11 required. Found {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"Python version check passed: {sys.version}")
    return True

def create_venv(venv_dir="venv"):
    """Create a virtual environment in the specified directory."""
    venv_path = Path(venv_dir)
    if venv_path.exists():
        print(f"Virtual environment at {venv_path} already exists. Skipping creation.")
        return str(venv_path)
    
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("Virtual environment created successfully.")
    return str(venv_path)

def install_dependencies(venv_dir="venv", requirements_file="code/requirements.txt"):
    """Install dependencies from requirements.txt into the virtual environment."""
    venv_path = Path(venv_dir)
    if not venv_path.exists():
        print(f"Error: Virtual environment not found at {venv_path}. Run create_venv first.")
        sys.exit(1)

    # Determine the correct pip path based on OS
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        sys.exit(1)

    requirements_path = Path(requirements_file)
    if not requirements_path.exists():
        print(f"Error: Requirements file not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    # Upgrade pip first
    subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
    
    # Install requirements
    result = subprocess.run(
        [str(pip_path), "install", "-r", str(requirements_path)],
        check=True
    )
    
    if result.returncode == 0:
        print("Dependencies installed successfully.")
        # Log installed packages
        subprocess.run([str(pip_path), "freeze"], check=False)
    else:
        print("Error installing dependencies.")
        sys.exit(1)

    return True

def main():
    """Main entry point for environment initialization."""
    print("=== Initializing Python 3.11 Virtual Environment ===")
    
    # Step 1: Check Python version
    check_python_version()
    
    # Step 2: Create virtual environment
    venv_path = create_venv()
    
    # Step 3: Install dependencies
    install_dependencies(venv_path)
    
    print("=== Environment Setup Complete ===")
    print(f"Activate the environment with:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()
