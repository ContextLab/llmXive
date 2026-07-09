import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Creates a Python virtual environment in the repository root.
    Uses python3.11 if available, otherwise falls back to the current python interpreter.
    """
    root_dir = Path(__file__).resolve().parent.parent
    venv_path = root_dir / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return

    python_exe = "python3.11"
    try:
        # Check if python3.11 exists
        subprocess.run([python_exe, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"python3.11 not found. Using current interpreter: {sys.executable}")
        python_exe = sys.executable

    print(f"Creating virtual environment at {venv_path} using {python_exe}...")
    result = subprocess.run([python_exe, "-m", "venv", str(venv_path)])

    if result.returncode != 0:
        print(f"Error: Failed to create virtual environment (exit code {result.returncode})")
        sys.exit(1)

    print("Virtual environment created successfully.")
    print("Activate it with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")

if __name__ == "__main__":
    main()