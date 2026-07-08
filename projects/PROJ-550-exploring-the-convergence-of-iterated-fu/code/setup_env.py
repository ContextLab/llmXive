"""
Script to initialize the Python environment for PROJ-550.
Installs dependencies from requirements.txt and updates it with frozen versions.
"""
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e.stderr.decode()}")
        sys.exit(1)

    print("Freezing installed packages to requirements.txt...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,
            stdout=open(requirements_path, "w"),
            stderr=subprocess.PIPE,
        )
        print("requirements.txt updated with frozen versions.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to freeze packages: {e.stderr.decode()}")
        sys.exit(1)

if __name__ == "__main__":
    main()