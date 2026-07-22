"""
Initialize the Python project environment for PROJ-550.
This script creates requirements.txt with pinned versions,
installs dependencies, and freezes the environment.
"""
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    # Define pinned versions as per task specification
    pinned_versions = [
        "numpy==1.26.4",
        "scipy==1.12.0",
        "scikit-learn==1.4.0",
        "pandas==2.1.4",
        "pytest==7.4.3",
        "matplotlib==3.8.2",
        "pyarrow==14.0.1",
    ]

    print(f"Creating {requirements_path}...")
    with open(requirements_path, "w") as f:
        f.write("\n".join(pinned_versions) + "\n")
    print("requirements.txt created successfully.")

    print("Installing dependencies...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
        check=True,
        capture_output=False
    )

    print("Freezing environment to requirements.txt...")
    freeze_result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        check=True,
        capture_output=True,
        text=True
    )

    with open(requirements_path, "w") as f:
        f.write(freeze_result.stdout)

    print("Environment initialized successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())