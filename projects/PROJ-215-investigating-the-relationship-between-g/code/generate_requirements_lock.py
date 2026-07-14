"""
Script to generate a deterministic requirements.lock file from requirements.txt.

This ensures reproducibility by resolving exact versions of all dependencies
and their sub-dependencies.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Generate requirements.lock using pip-tools or pip freeze."""
    project_root = Path(__file__).parent.parent
    requirements_txt = project_root / "requirements.txt"
    requirements_lock = project_root / "requirements.lock"

    if not requirements_txt.exists():
        print("Error: requirements.txt not found in project root.")
        sys.exit(1)

    print(f"Resolving dependencies from {requirements_txt}...")

    # Strategy 1: Try pip-compile (pip-tools) if available
    try:
        subprocess.run(
            [sys.executable, "-m", "piptools", "compile", "--generate-hashes", 
             str(requirements_txt), "-o", str(requirements_lock)],
            check=True,
            capture_output=False
        )
        print(f"Successfully generated {requirements_lock} using pip-compile.")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Strategy 2: Fallback to pip freeze (less deterministic for sub-deps, but works)
    # We install requirements first to ensure environment is consistent
    print("Falling back to pip install + freeze method...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_txt)],
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

    # Freeze the current environment to the lock file
    with open(requirements_lock, "w", encoding="utf-8") as f:
        f.write("# Auto-generated lock file via generate_requirements_lock.py\n")
        f.write("# Run: pip install -r requirements.lock\n\n")
        subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            stdout=f,
            check=True
        )

    print(f"Successfully generated {requirements_lock} using pip freeze.")

if __name__ == "__main__":
    main()