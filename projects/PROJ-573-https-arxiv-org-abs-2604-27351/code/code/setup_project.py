"""
Setup script for the Heterogeneous Scientific Foundation Model Collaboration Benchmark project.
Initializes Python 3.11 environment and installs dependencies.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"ERROR: Python 3.11+ is required. Current version: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python version check passed: {version.major}.{version.minor}.{version.micro}")
    return True

def create_venv(venv_path="code/.venv"):
    """Create a virtual environment in the specified path."""
    venv_path = Path(venv_path)
    if venv_path.exists():
        print(f"✓ Virtual environment already exists at {venv_path}")
        return venv_path
    
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print(f"✓ Virtual environment created successfully")
    return venv_path

def install_requirements(venv_path="code/.venv"):
    """Install dependencies from requirements.txt."""
    venv_path = Path(venv_path)
    pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip"
    requirements_path = Path("code/requirements.txt")
    
    if not requirements_path.exists():
        print("WARNING: requirements.txt not found. Skipping dependency installation.")
        return
    
    print(f"Installing dependencies from {requirements_path}...")
    subprocess.run([str(pip_path), "install", "-r", str(requirements_path), "--upgrade"], check=True)
    print("✓ Dependencies installed successfully")

def verify_installation(venv_path="code/.venv"):
    """Verify that the virtual environment is correctly set up."""
    venv_path = Path(venv_path)
    python_path = venv_path / "bin" / "python" if os.name != "nt" else venv_path / "Scripts" / "python"
    
    if not python_path.exists():
        print(f"ERROR: Python executable not found at {python_path}")
        return False
    
    result = subprocess.run([str(python_path), "--version"], capture_output=True, text=True)
    print(f"✓ Verified Python executable: {result.stdout.strip()}")
    return True

def main():
    """Main setup function."""
    print("=" * 60)
    print("Heterogeneous Scientific Foundation Model Collaboration Benchmark")
    print("Setup Script")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    venv_path = create_venv()
    
    # Install requirements
    install_requirements(venv_path)
    
    # Verify installation
    if verify_installation(venv_path):
        print("\n" + "=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print(f"\nTo activate the virtual environment, run:")
        if os.name == "nt":
            print(f"  {venv_path}\\Scripts\\activate")
        else:
            print(f"  source {venv_path}/bin/activate")
    else:
        print("\nERROR: Setup failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
