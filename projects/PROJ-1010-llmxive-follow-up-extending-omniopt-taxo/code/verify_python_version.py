"""
Verify that the current Python environment is version 3.11 or higher.

This script is a prerequisite check for the llmXive project.
It exits with code 0 if the version is valid, or code 1 if not.
"""
import sys
import subprocess

MIN_MAJOR = 3
MIN_MINOR = 11

def check_version() -> bool:
    """Check if the running Python interpreter meets the minimum version requirement."""
    current_major = sys.version_info.major
    current_minor = sys.version_info.minor

    if current_major > MIN_MAJOR:
        return True
    if current_major == MIN_MAJOR and current_minor >= MIN_MINOR:
        return True
    
    return False

def get_python_executable() -> str:
    """Attempt to find the 'python3' executable in the PATH."""
    try:
        result = subprocess.run(
            ["python3", "--version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "python3 not found in PATH"
    except FileNotFoundError:
        return "python3 command not found"

def main() -> int:
    """Main entry point for the version verification script."""
    print(f"Current Python executable: {sys.executable}")
    print(f"Current Python version: {sys.version}")
    
    if not check_version():
        print(f"ERROR: Python version {sys.version_info.major}.{sys.version_info.minor} is too old.")
        print(f"Requirement: Python {MIN_MAJOR}.{MIN_MINOR} or higher.")
        return 1
    
    print(f"SUCCESS: Python version {sys.version_info.major}.{sys.version_info.minor} meets the requirement (>= {MIN_MAJOR}.{MIN_MINOR}).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
