"""
Script to install dependencies from requirements.txt into a virtual environment
and verify the installation by listing installed packages.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Determine project root relative to this script's location
    # Script is at: projects/PROJ-.../code/setup/install_deps.py
    # requirements.txt is at: projects/PROJ-.../requirements.txt
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    requirements_path = project_root / "requirements.txt"
    venv_path = project_root / ".venv"

    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Project root: {project_root}")
    print(f"Requirements file: {requirements_path}")
    print(f"Virtual environment path: {venv_path}")

    # Step 1: Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment already exists.")

    # Determine the path to the pip executable inside the venv
    # Handle both Windows (Scripts) and Unix-like (bin)
    if os.name == 'nt':
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    if not pip_executable.exists():
        print(f"ERROR: pip executable not found at {pip_executable}")
        sys.exit(1)

    # Step 2: Upgrade pip first (optional but good practice)
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to upgrade pip: {e}")
        # Continue anyway, as it might not be critical

    # Step 3: Install dependencies from requirements.txt
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        # Print stderr for debugging
        print(f"ERROR: Failed to install dependencies: {e}")
        if e.stderr:
            print(e.stderr.decode())
        sys.exit(1)

    # Step 4: Verify installation by listing packages
    print("\nVerifying installation by listing packages...")
    try:
        result = subprocess.run(
            [str(python_executable), "-m", "pip", "list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("\nInstalled packages:")
        print(result.stdout)
        
        # Basic verification: check if key packages are present
        required_packages = [
            "pandas", "numpy", "scipy", "statsmodels", 
            "scikit-learn", "pyyaml", "requests", "joblib", "pytest"
        ]
        output_lower = result.stdout.lower()
        missing = []
        for pkg in required_packages:
            # Check if package name appears in the list (case-insensitive)
            if not any(pkg in line.lower() for line in output_lower.split('\n')):
                missing.append(pkg)
        
        if missing:
            print(f"\nWARNING: The following packages were not found in pip list: {missing}")
            # We don't exit here as the command ran successfully, 
            # but this alerts the user.
        else:
            print("\nAll required packages appear to be installed.")
            
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to list packages: {e}")
        sys.exit(1)

    print("\nInstallation and verification completed successfully.")

if __name__ == "__main__":
    main()