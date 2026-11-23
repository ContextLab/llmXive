import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Verify Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"Error: Python 3.11+ is required. Found Python {version.major}.{version.minor}")
        sys.exit(1)
    print(f"Python version check passed: {version.major}.{version.minor}.{version.micro}")

def install_dependencies(requirements_path: str = "code/requirements.txt"):
    """Install dependencies from requirements.txt."""
    if not os.path.exists(requirements_path):
        print(f"Error: Requirements file not found at {requirements_path}")
        sys.exit(1)
    
    print(f"Installing dependencies from {requirements_path}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", requirements_path],
        check=False
    )
    if result.returncode != 0:
        print("Error: Failed to install dependencies")
        sys.exit(1)
    print("Dependencies installed successfully.")

def run_pip_check():
    """Run pip check to verify no dependency conflicts."""
    print("Running pip check...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        check=False
    )
    if result.returncode != 0:
        # pip check returns 1 if there are broken dependencies
        print("Warning: pip check found broken dependencies:")
        print(result.stdout.decode() if result.stdout else "")
        print(result.stderr.decode() if result.stderr else "")
        # We do not exit here as pip check is a verification step, not a blocker for installation
        return False
    print("pip check passed: No broken dependencies found.")
    return True

def main():
    """Main entry point for environment verification."""
    print("=== Project Environment Verification ===")
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Verify dependencies
    run_pip_check()
    
    print("=== Verification Complete ===")

if __name__ == "__main__":
    main()
