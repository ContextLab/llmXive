"""
Environment setup and dependency verification script.
Checks Python version and ensures required dependencies are installed.
"""
import sys
import subprocess
from pathlib import Path

def check_python_version(min_version: tuple = (3, 9)) -> bool:
    """
    Check if the current Python version meets the minimum requirement.
    
    Args:
        min_version: Minimum required version tuple (major, minor).
        
    Returns:
        bool: True if version is sufficient, False otherwise.
    """
    current_version = (sys.version_info.major, sys.version_info.minor)
    if current_version < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]}+ is required. "
              f"Current version: {sys.version}")
        return False
    print(f"Python version check passed: {sys.version.split()[0]}")
    return True

def check_dependencies(requirements_path: Path) -> bool:
    """
    Check if all dependencies listed in requirements.txt are installed.
    
    Args:
        requirements_path: Path to the requirements.txt file.
        
    Returns:
        bool: True if all dependencies are installed, False otherwise.
    """
    if not requirements_path.exists():
        print(f"Error: Requirements file not found at {requirements_path}")
        return False

    try:
        # Read requirements
        with open(requirements_path, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not requirements:
            print("Warning: No dependencies found in requirements.txt")
            return True

        # Check each requirement
        missing = []
        for req in requirements:
            # Handle version specifiers by stripping them for import check
            pkg_name = req.split('>=')[0].split('<=')[0].split('==')[0].split('[')[0].strip()
            try:
                __import__(pkg_name.lower().replace('-', '_'))
            except ImportError:
                missing.append(req)

        if missing:
            print("Missing dependencies detected:")
            for dep in missing:
                print(f"  - {dep}")
            print("\nRun: pip install -r requirements.txt")
            return False

        print(f"All {len(requirements)} dependencies verified.")
        return True

    except Exception as e:
        print(f"Error checking dependencies: {e}")
        return False

def main():
    """Main entry point for environment setup verification."""
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    print("=== Environment Setup Verification ===")
    
    version_ok = check_python_version()
    if not version_ok:
        sys.exit(1)

    deps_ok = check_dependencies(requirements_path)
    if not deps_ok:
        sys.exit(1)

    print("=== Environment Ready ===")

if __name__ == "__main__":
    main()