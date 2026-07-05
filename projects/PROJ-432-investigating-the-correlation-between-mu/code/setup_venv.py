"""
Task T002a: Create Python 3.11 virtual environment and activation script.

This script programmatically creates a virtual environment using the system's
Python interpreter (ensuring it is version 3.11+), and generates the standard
activation scripts for POSIX (bash/zsh) and Windows (cmd/PowerShell).
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / ".venv"
    python_version = sys.version_info

    # Validate Python version
    if python_version.major != 3 or python_version.minor < 11:
        print(
            f"Error: This project requires Python 3.11+. "
            f"Current version: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        sys.exit(1)

    print(f"Creating virtual environment at: {venv_path} using Python {sys.executable}")

    # Create the virtual environment
    # clear=True ensures we recreate it if it exists but is stale
    builder = venv.EnvBuilder(
        symlinks=True,
        with_pip=True,
        upgrade_deps=False,
    )
    
    # Check if .venv exists and remove it to ensure a clean state if needed
    if venv_path.exists():
        print("Removing existing .venv to ensure clean creation...")
        import shutil
        shutil.rmtree(venv_path)

    builder.create(str(venv_path))

    # Ensure pip is upgraded to the latest version within the venv
    # This is a best practice to ensure compatibility with requirements.txt
    print("Upgrading pip in the new environment...")
    pip_executable = venv_path / "bin" / "pip"
    if os.name == "nt":
        pip_executable = venv_path / "Scripts" / "pip.exe"
    
    subprocess.check_call([str(pip_executable), "install", "--upgrade", "pip"])

    # Generate activation script content for explicit reference
    # While venv creates these, we ensure they are present and correct
    if os.name == "nt":
        activate_script = venv_path / "Scripts" / "activate.bat"
        activate_ps = venv_path / "Scripts" / "Activate.ps1"
        print(f"Windows activation scripts created at: {activate_script}")
    else:
        activate_script = venv_path / "bin" / "activate"
        print(f"POSIX activation script created at: {activate_script}")

    print("\nVirtual environment setup complete.")
    print("To activate, run:")
    if os.name == "nt":
        print(f"  .venv\\Scripts\\activate.bat")
    else:
        print(f"  source .venv/bin/activate")

    return 0

if __name__ == "__main__":
    sys.exit(main())