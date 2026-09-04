import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Install project dependencies from requirements.txt into the current virtual environment.
    This script is designed to be run after the virtual environment is activated.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Install pip first to ensure it's up to date
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
        
        print("Dependencies installed successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()