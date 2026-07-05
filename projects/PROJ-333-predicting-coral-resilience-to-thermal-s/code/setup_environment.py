"""
Setup script for the Coral Resilience project.
This script verifies the environment, installs Python dependencies,
and checks for PLINK2 availability.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a shell command and print status."""
    print(f"Checking: {description}...")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"  [OK] {description} found: {result.stdout.strip()[:50]}...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [FAIL] {description} not found or failed.")
        if e.stderr:
            print(f"     Error: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        print(f"  [FAIL] {description} command not found.")
        return False

def check_python_version():
    """Verify Python version is 3.11 or compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 11:
        return True
    elif version.major > 3:
        return True
    else:
        print("WARNING: Python 3.11+ is recommended for this project.")
        return True  # Allow to proceed but warn

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    requirements_path = "requirements.txt"
    if not os.path.exists(requirements_path):
        print(f"ERROR: {requirements_path} not found in project root.")
        return False

    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies.")
        return False

def verify_plink2():
    """Check if PLINK2 is installed."""
    return run_command("plink2 --version", "PLINK2")

def main():
    print("--- Coral Resilience Project Environment Setup ---")
    
    if not check_python_version():
        sys.exit(1)

    if not install_dependencies():
        sys.exit(1)

    if not verify_plink2():
        print("\nWARNING: PLINK2 is not installed.")
        print("Please run 'code/install_plink2.sh' or install manually.")
        print("The pipeline requires PLINK2 for GWAS analysis.")
        # Do not exit here, as the user might install it later
        # but we flag it clearly.
    
    print("\n--- Setup Complete ---")
    print("Next steps:")
    print("  1. Ensure PLINK2 is installed (see warning above if missing).")
    print("  2. Run the data ingestion pipeline.")

if __name__ == "__main__":
    main()