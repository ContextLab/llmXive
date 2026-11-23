"""
Verify Python 3.11+ availability for the llmXive research pipeline.

This script checks that the current Python environment meets the
minimum version requirement (3.11) and reports the executable path.
"""
import sys
import subprocess
from typing import Tuple, Optional

MIN_VERSION = (3, 11)

def get_python_executable() -> str:
    """Return the path to the current Python executable."""
    return sys.executable

def check_version() -> Tuple[bool, str]:
    """
    Check if the current Python version meets the minimum requirement.
    
    Returns:
        Tuple of (is_valid, message)
    """
    current_version = sys.version_info[:2]
    version_str = f"{current_version[0]}.{current_version[1]}"
    min_version_str = f"{MIN_VERSION[0]}.{MIN_VERSION[1]}"
    
    if current_version >= MIN_VERSION:
        return True, f"Python {version_str} meets minimum requirement ({min_version_str})"
    else:
        return False, f"Python {version_str} is below minimum requirement ({min_version_str})"

def main() -> int:
    """
    Main entry point for version verification.
    
    Returns:
        Exit code: 0 for success, 1 for failure
    """
    executable = get_python_executable()
    is_valid, message = check_version()
    
    print(f"Python Executable: {executable}")
    print(f"Current Version: {sys.version}")
    print(f"Verification Result: {message}")
    
    if is_valid:
        print("✓ Version check PASSED")
        return 0
    else:
        print("✗ Version check FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())