import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize virtualenv in project root:
    1. Check Python version >= 3.10
    2. Check requirements.txt exists
    3. Run: python -m venv .venv
    4. Activate venv and install requirements.txt
    
    Exits with code 1 if requirements.txt is missing or Python < 3.10.
    """
    # Determine project root (parent of code/)
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"
    venv_path = project_root / ".venv"
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("ERROR: Python version must be 3.10 or higher.", file=sys.stderr)
        sys.exit(1)
    
    # Check requirements.txt exists
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Initializing virtualenv at {venv_path}...")
    
    # Create virtualenv
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtualenv: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    
    # Determine activate script path based on OS
    if os.name == "nt":  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    if not activate_script.exists():
        print(f"ERROR: Activate script not found at {activate_script}", file=sys.stderr)
        sys.exit(1)
    
    # Install requirements using the venv's pip directly
    print("Installing dependencies from requirements.txt...")
    try:
        # Use pip from the virtualenv directly to avoid shell activation issues
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install requirements: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    
    print("Virtualenv setup complete. Dependencies installed.")
    print(f"To activate, run: source {activate_script} (Unix) or {activate_script} (Windows)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())