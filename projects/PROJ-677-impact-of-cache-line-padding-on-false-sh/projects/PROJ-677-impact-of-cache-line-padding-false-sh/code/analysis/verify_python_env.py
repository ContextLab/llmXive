#!/usr/bin/env python3
"""
Verify Python 3.11+ environment and required dependencies.
This script ensures the analysis environment is properly configured.
"""

import sys
import subprocess
from typing import List, Tuple

REQUIRED_PACKAGES = [
    "pandas",
    "scipy",
    "matplotlib",
    "pydantic",
    "pyyaml",
]

def check_python_version() -> bool:
    """Check if Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"ERROR: Python 3.11+ required. Found: {version.major}.{version.minor}")
        return False
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_packages() -> Tuple[bool, List[str]]:
    """Check if all required packages are installed."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} missing")
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False, missing
    return True, []

def main() -> int:
    """Main entry point."""
    print("=== Python Environment Verification ===")
    
    if not check_python_version():
        return 1
    
    all_present, missing = check_packages()
    if not all_present:
        return 1
    
    print("\n=== Environment Ready ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
