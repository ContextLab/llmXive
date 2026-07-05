import subprocess
import sys
import os
from pathlib import Path

def main():
    """Create a virtual environment at .venv."""
    root = Path(__file__).resolve().parent.parent
    venv_path = root / ".venv"
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        return
    print(f"Creating virtual environment at {venv_path}...")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
    print("Virtual environment created successfully.")

if __name__ == "__main__":
    main()