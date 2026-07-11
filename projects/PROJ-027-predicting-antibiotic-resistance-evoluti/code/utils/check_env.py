"""
Environment verification script for PROJ-027.
Verifies that all required packages listed in requirements.txt are installed
and compatible (via pip check).
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Verifying environment at: {project_root}")
    print(f"Reading dependencies from: {requirements_path}")

    # Install/Upgrade dependencies
    print("\n--- Installing dependencies ---")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--quiet"],
            check=True
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

    # Run pip check
    print("\n--- Running pip check ---")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        print("Environment verification passed: No broken dependencies found.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: pip check failed. Broken dependencies detected:")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())