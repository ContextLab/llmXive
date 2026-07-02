import subprocess
import sys
import importlib.util
from pathlib import Path

def check_package(package_name):
    """Check if a package is installed in the current environment."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_dependencies(dependencies):
    """Install a list of dependencies using pip."""
    if not dependencies:
        return
    cmd = [sys.executable, "-m", "pip", "install"] + dependencies
    subprocess.check_call(cmd)

def verify_dependencies():
    """
    Verifies that required dependencies for linting are installed.
    Returns True if all are present, False otherwise.
    """
    required = ["flake8", "black"]
    missing = [pkg for pkg in required if not check_package(pkg)]
    if missing:
        print(f"Missing dependencies: {missing}")
        return False
    return True

# Note: The main requirements.txt is managed by T002, 
# but this module provides the utility functions needed by setup_linting.py