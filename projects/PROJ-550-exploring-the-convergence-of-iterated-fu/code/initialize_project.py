"""
Script to initialize the Python project environment.

This script performs the following actions:
1. Creates a requirements.txt file with the specific pinned versions required.
2. Attempts to install these dependencies via pip.
3. Regenerates requirements.txt via pip freeze to ensure exact match with installed environment.

Note: This script is designed to be run from the project root directory
(projects/PROJ-550-exploring-the-convergence-of-iterated-fu).
"""
import subprocess
import sys
from pathlib import Path

def main():
    # Define the project root relative to this script's location or CWD
    # Assuming this script is placed in code/ or root. We target the current working directory.
    root_dir = Path.cwd()
    requirements_path = root_dir / "requirements.txt"

    # Define the specific pinned versions as requested in T002
    pinned_packages = [
        "numpy==1.26.4",
        "scipy==1.12.0",
        "scikit-learn==1.4.0",
        "pandas==2.1.4",
        "pytest==7.4.3",
        "matplotlib==3.8.2",
        "pyarrow==14.0.1",
    ]

    # Step 1: Write initial requirements.txt
    print(f"Writing initial requirements.txt to: {requirements_path}")
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write("\n".join(pinned_packages) + "\n")

    # Step 2: Run pip install
    print("Running pip install -r requirements.txt...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=False,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: pip install failed with return code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

    # Step 3: Run pip freeze to overwrite requirements.txt with actual installed versions
    # This ensures the file reflects the exact environment state, resolving any
    # potential minor version differences if the pinned versions were unavailable.
    print("Running pip freeze to regenerate requirements.txt...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,
            capture_output=True,
            text=True
        )
        with open(requirements_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        print(f"Successfully updated {requirements_path} with pip freeze output.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: pip freeze failed with return code {e.returncode}")
        sys.exit(1)

    print("Project initialization complete.")

if __name__ == "__main__":
    main()
