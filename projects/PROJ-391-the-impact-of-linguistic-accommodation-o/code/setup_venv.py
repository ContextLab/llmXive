import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Creates a virtual environment in code/.venv if it does not already exist.
    Does not attempt to 'activate' it in the current shell process, as that
    is a shell-specific operation. Instead, it ensures the directory structure
    and activation scripts exist so they can be used in subsequent steps.
    """
    # Determine the project root (assuming script is in code/)
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    venv_path = script_dir / ".venv"
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
    else:
        print(f"Creating virtual environment at {venv_path}...")
        try:
            # Use the same Python interpreter running this script
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Verify activation script existence
    if sys.platform == "win32":
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:
        activate_script = venv_path / "bin" / "activate"
    
    if not activate_script.exists():
        print(f"Error: Activation script not found at {activate_script}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Activation script available at: {activate_script}")
    print("To activate, run: source code/.venv/bin/activate (Linux/Mac) or code\\.venv\\Scripts\\activate.bat (Windows)")

if __name__ == "__main__":
    main()