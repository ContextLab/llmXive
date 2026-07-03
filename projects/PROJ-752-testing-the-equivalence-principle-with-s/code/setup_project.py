import os
import sys
import subprocess
import shutil

def main():
    """
    Initialize the Python project environment.
    This script verifies Python version and installs dependencies from requirements.txt.
    """
    # Check Python version
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)

    print(f"Python version verified: {sys.version}")

    # Determine project root (assuming script is in code/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    requirements_path = os.path.join(project_root, "requirements.txt")

    if not os.path.exists(requirements_path):
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Found requirements.txt at {requirements_path}")

    # Install dependencies
    print("Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path],
            cwd=project_root
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

    # Verify directory structure exists (T001 should have created this, but ensure it)
    dirs = [
        "code/data", "code/models", "code/analysis", "code/utils", "code/tests",
        "contracts", "data/raw", "data/processed", "data/results", "docs"
    ]
    for d in dirs:
        path = os.path.join(project_root, d)
        os.makedirs(path, exist_ok=True)

    print("Project initialization complete.")

if __name__ == "__main__":
    main()
