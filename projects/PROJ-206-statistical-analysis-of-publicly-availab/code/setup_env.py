import os
import subprocess
import sys
from pathlib import Path

def ensure_virtual_environment(venv_path: str = ".venv") -> bool:
    """
    Create a virtual environment if it doesn't exist.
    
    Args:
        venv_path: Path to the virtual environment directory
        
    Returns:
        True if venv exists or was created successfully, False otherwise
    """
    venv_dir = Path(venv_path)
    
    if venv_dir.exists() and (venv_dir / "pyvenv.cfg").exists():
        print(f"Virtual environment already exists at {venv_path}")
        return True
    
    try:
        print(f"Creating virtual environment at {venv_path}...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error creating virtual environment: {e}")
        return False


def install_dependencies(requirements_path: str = "requirements.txt", venv_path: str = ".venv") -> bool:
    """
    Install dependencies from requirements.txt into the virtual environment.
    
    Args:
        requirements_path: Path to requirements.txt file
        venv_path: Path to the virtual environment directory
        
    Returns:
        True if installation succeeded, False otherwise
    """
    venv_dir = Path(venv_path)
    requirements_file = Path(requirements_path)
    
    if not requirements_file.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False
    
    if not venv_dir.exists():
        print(f"Error: Virtual environment not found at {venv_path}. Run ensure_virtual_environment first.")
        return False
    
    # Determine the pip executable path based on OS
    if os.name == "nt":  # Windows
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        pip_path = venv_dir / "bin" / "pip"
    
    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        return False
    
    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.check_call([str(pip_path), "install", "--upgrade", "pip"])
        
        # Install requirements
        print(f"Installing packages from {requirements_path}...")
        subprocess.check_call([str(pip_path), "install", "-r", str(requirements_file)])
        
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error installing dependencies: {e}")
        return False


def main():
    """
    Main entry point for setting up the virtual environment and installing dependencies.
    """
    print("=" * 60)
    print("Setting up Python Virtual Environment")
    print("=" * 60)
    
    # Ensure virtual environment exists
    if not ensure_virtual_environment():
        print("Failed to set up virtual environment. Exiting.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    print("=" * 60)
    print("Setup complete!")
    print("To activate the virtual environment, run:")
    if os.name == "nt":
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    print("=" * 60)


if __name__ == "__main__":
    main()
