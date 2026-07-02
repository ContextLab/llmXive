"""
T002: Initialize Python 3.11 virtualenv and install dependencies.

This script automates the creation of a virtual environment and installs
the dependencies listed in code/requirements.txt.
"""
import os
import subprocess
import sys
import venv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_DIR = os.path.join(PROJECT_ROOT, ".venv")
REQUIREMENTS_PATH = os.path.join(PROJECT_ROOT, "code", "requirements.txt")

def check_python_version():
    """Ensure the running Python is 3.11."""
    if sys.version_info[:2] != (3, 11):
        print(f"⚠️  Warning: Running Python {sys.version_info.major}.{sys.version_info.minor}, "
              f"but Python 3.11 is recommended for compatibility.")
        # We proceed anyway to allow flexibility, but warn.

def create_venv():
    """Create the virtual environment if it doesn't exist."""
    if os.path.exists(VENV_DIR):
        print(f"✅ Virtual environment already exists at {VENV_DIR}")
        return True
    
    print(f"📦 Creating virtual environment at {VENV_DIR}...")
    try:
        venv.create(VENV_DIR, with_pip=True, clear=False)
        print("✅ Virtual environment created successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install requirements from code/requirements.txt."""
    if not os.path.exists(REQUIREMENTS_PATH):
        print(f"❌ Error: Requirements file not found at {REQUIREMENTS_PATH}")
        return False

    # Determine the pip executable path based on OS
    if sys.platform == "win32":
        pip_executable = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        pip_executable = os.path.join(VENV_DIR, "bin", "pip")

    if not os.path.exists(pip_executable):
        print(f"❌ Error: pip executable not found at {pip_executable}")
        return False

    print(f"🚀 Upgrading pip and installing dependencies from {REQUIREMENTS_PATH}...")
    
    # Upgrade pip first
    subprocess.run([pip_executable, "install", "--upgrade", "pip"], check=True)
    
    # Install requirements
    try:
        subprocess.run([pip_executable, "install", "-r", REQUIREMENTS_PATH], check=True)
        print("✅ Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    print("🚀 Starting T002: Virtual Environment Initialization")
    check_python_version()
    
    if not create_venv():
        return 1
    
    if not install_dependencies():
        return 1
    
    print("✅ T002 Completed: Virtual environment initialized and dependencies installed.")
    print(f"   To activate, run: source {os.path.join(VENV_DIR, 'bin', 'activate')} (Linux/Mac)")
    print(f"   or: {os.path.join(VENV_DIR, 'Scripts', 'activate')} (Windows)")
    return 0

if __name__ == "__main__":
    sys.exit(main())