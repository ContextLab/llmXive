import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_python_version():
    """Check if the current Python version is 3.11.x."""
    version = sys.version_info
    if version.major == 3 and version.minor == 11:
        print(f"Python version {version.major}.{version.minor}.{version.micro} is valid (3.11.x).")
        return True
    else:
        print(f"ERROR: Python version {version.major}.{version.minor}.{version.micro} is not 3.11.x.")
        print("Please ensure python3.11 is available in your PATH or set PYVENV_PYTHON=python3.11")
        return False

def create_virtual_environment(venv_path: Path):
    """Create a virtual environment in the specified path."""
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)
    
    print(f"Creating virtual environment at {venv_path}...")
    
    # Try to use the current interpreter first, but allow override
    python_exec = os.environ.get('PYVENV_PYTHON', sys.executable)
    
    try:
        result = subprocess.run(
            [python_exec, '-m', 'venv', str(venv_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e.stderr}")
        return False

def install_dependencies(venv_path: Path, requirements_path: Path):
    """Install dependencies from requirements.txt into the virtual environment."""
    if not requirements_path.exists():
        print(f"ERROR: Requirements file not found at {requirements_path}")
        return False

    venv_bin = venv_path / 'bin'
    pip_path = venv_bin / 'pip'
    
    if not pip_path.exists():
        print(f"ERROR: pip not found in virtual environment at {pip_path}")
        return False

    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Upgrade pip first
        subprocess.run(
            [str(pip_path), 'install', '--upgrade', 'pip'],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Install requirements
        result = subprocess.run(
            [str(pip_path), 'install', '-r', str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e.stderr}")
        return False

def verify_installation(venv_path: Path):
    """Verify the virtual environment is working and Python version is 3.11.x."""
    python_path = venv_path / 'bin' / 'python'
    
    if not python_path.exists():
        print(f"ERROR: Python executable not found at {python_path}")
        return False

    try:
        result = subprocess.run(
            [str(python_path), '--version'],
            check=True,
            capture_output=True,
            text=True
        )
        version_output = result.stdout.strip()
        print(f"Verification: {version_output}")
        
        # Parse version to check it's 3.11.x
        version_parts = version_output.replace('Python ', '').split('.')
        if len(version_parts) >= 2:
            major = int(version_parts[0])
            minor = int(version_parts[1])
            if major == 3 and minor == 11:
                print("SUCCESS: Virtual environment is using Python 3.11.x")
                return True
            else:
                print(f"ERROR: Virtual environment is using Python {major}.{minor}, expected 3.11.x")
                return False
        else:
            print(f"ERROR: Could not parse version string: {version_output}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to verify installation: {e.stderr}")
        return False

def main():
    """Main function to set up the virtual environment."""
    # Determine paths relative to code/ directory
    code_dir = Path(__file__).parent
    venv_path = code_dir / '.venv'
    requirements_path = code_dir / 'requirements.txt'
    
    print("=" * 60)
    print("Setting up Python 3.11 Virtual Environment")
    print("=" * 60)
    
    # Step 1: Check Python version
    if not check_python_version():
        print("Exiting due to incorrect Python version.")
        sys.exit(1)
    
    # Step 2: Create virtual environment
    if not create_virtual_environment(venv_path):
        print("Exiting due to virtual environment creation failure.")
        sys.exit(1)
    
    # Step 3: Install dependencies
    if not install_dependencies(venv_path, requirements_path):
        print("Exiting due to dependency installation failure.")
        sys.exit(1)
    
    # Step 4: Verify installation
    if not verify_installation(venv_path):
        print("Exiting due to verification failure.")
        sys.exit(1)
    
    print("=" * 60)
    print("Virtual environment setup complete!")
    print(f"Activate with: source {venv_path}/bin/activate")
    print("=" * 60)

if __name__ == '__main__':
    main()
