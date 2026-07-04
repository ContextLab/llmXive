"""
Setup script to create the foundational directory structure and requirements file.
This script fulfills tasks T001a, T001b, T001c, T001d, and T002a.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to this script (assuming script is in code/)
    # The task implies a repository root structure, but the API surface shows files in `code/`.
    # We will create the structure relative to the current working directory (assumed to be project root or code root).
    # Based on the API surface `code/setup_data_dirs.py`, we assume the script runs from the project root or code root.
    # To be safe and align with the "code/" prefix in the API surface, we assume the script is run from the project root.
    
    project_root = Path.cwd()
    
    # Check if we are in the 'code' directory or project root.
    # The API surface lists files like 'code/setup_data_dirs.py'.
    # If this script is at 'code/setup_directories.py', we need to ensure we are creating 'src' relative to 'code'.
    
    current_file = Path(__file__).resolve()
    if current_file.parent.name == "code":
        base_dir = current_file.parent
    else:
        base_dir = project_root / "code"

    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    # Directories to create (T001a - T001d)
    # Note: T001a asks for 'src/', T001b 'tests/', T001c 'data/', T001d 'state/'
    # Based on the API surface, these are under 'code/'.
    dirs_to_create = [
        base_dir / "src",
        base_dir / "tests",
        base_dir / "data",
        base_dir / "state"
    ]

    # Create directories
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked
        (dir_path / ".gitkeep").touch()
        print(f"Created directory: {dir_path}")

    # Create requirements.txt (T002a)
    requirements_path = base_dir / "requirements.txt"
    if not requirements_path.exists():
        with open(requirements_path, "w") as f:
            f.write(
                "pandas>=2.0.0\n"
                "numpy>=1.24.0\n"
                "scipy>=1.11.0\n"
                "pymc>=5.0.0\n"
                "arviz>=0.15.0\n"
                "requests>=2.31.0\n"
                "pyyaml>=6.0.0\n"
                "statsmodels>=0.14.0\n"
                "pytest>=7.4.0\n"
                "ruff>=0.1.0\n"
                "black>=23.0.0\n"
            )
        print(f"Created requirements.txt: {requirements_path}")
    else:
        print(f"requirements.txt already exists: {requirements_path}")

    print("Setup complete.")

if __name__ == "__main__":
    main()