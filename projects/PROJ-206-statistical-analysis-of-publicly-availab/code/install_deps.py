"""
Install dependencies from requirements.txt into the current virtual environment.

This script acts as the executable for task T002b. It verifies the existence
of requirements.txt and invokes pip to install the specified dependencies.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Execute the dependency installation."""
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        raise FileNotFoundError(
            f"requirements.txt not found at {requirements_path}. "
            "Ensure T002a has been completed."
        )

    print(f"Installing dependencies from: {requirements_path}")
    print("-" * 40)

    try:
        # Use the current python executable to ensure we install into the active venv
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("-" * 40)
            print("Dependency installation completed successfully.")
            return 0
        else:
            raise RuntimeError("pip installation failed with non-zero exit code.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())