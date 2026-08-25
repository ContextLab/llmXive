"""
Task T002a: Create Python 3.11 virtual environment and activation script.

This script creates a virtual environment in the project root using Python 3.11
and generates an activation script (activate.sh and activate.bat) for the user.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"
    
    print(f"Creating virtual environment at: {venv_path}")
    
    # Check Python version
    current_version = sys.version_info
    if current_version.major != 3 or current_version.minor < 10:
        print(f"Warning: Recommended Python version is 3.11, but found {sys.version}")
        print("Attempting to create venv anyway. If you have Python 3.11 installed,")
        print("you may need to run: python3.11 -m venv venv")
    
    try:
        # Create the virtual environment
        venv.create(venv_path, with_pip=True, clear=True)
        print("Virtual environment created successfully.")
        
        # Verify Python version inside venv
        if os.name == 'nt':
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        result = subprocess.run(
            [str(python_exe), "--version"],
            capture_output=True,
            text=True
        )
        print(f"Virtual environment Python version: {result.stdout.strip()}")
        
        # Create a helper script to activate the environment
        if os.name == 'nt':
            # Windows
            activate_script = venv_path / "activate.bat"
            if not activate_script.exists():
                # venv creates activate.bat, but we ensure it exists
                pass
            print("\nTo activate the environment on Windows, run:")
            print(f"  {venv_path}\\Scripts\\activate.bat")
        else:
            # Unix/Linux/Mac
            activate_script = venv_path / "bin" / "activate"
            if not activate_script.exists():
                print("Error: Activation script not found in bin/")
                return 1
            
            print("\nTo activate the environment on Unix/Linux/Mac, run:")
            print(f"  source {activate_script}")
            
            # Create a convenience wrapper script in the project root
            wrapper_path = project_root / "activate.sh"
            with open(wrapper_path, 'w') as f:
                f.write(f"""#!/bin/bash
# Convenience script to activate the virtual environment
SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"
""")
            wrapper_path.chmod(0o755)
            print(f"\nConvenience activation script created at: {wrapper_path}")
        
        print("\nNext steps:")
        print("1. Activate the virtual environment using the command above")
        print("2. Install dependencies: pip install -r requirements.txt")
        
        return 0
        
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())