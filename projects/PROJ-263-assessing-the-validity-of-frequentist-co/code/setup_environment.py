import sys
import subprocess
import importlib.util
from typing import List, Tuple

REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "scipy",
    "scikit-learn",
    "pyyaml",
    "pytest",
]

def check_python_version(min_version: Tuple[int, int, int] = (3, 11, 0)) -> bool:
    """Check if the current Python version meets the minimum requirement."""
    current = sys.version_info
    if (current.major, current.minor, current.micro) < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]}.{min_version[2]} or higher is required.")
        print(f"Current version: {current.major}.{current.minor}.{current.micro}")
        return False
    print(f"Python version check passed: {current.major}.{current.minor}.{current.micro}")
    return True

def check_packages(packages: List[str] = REQUIRED_PACKAGES) -> bool:
    """Check if all required packages are installed."""
    missing = []
    for pkg in packages:
        # Normalize package names for import (e.g., scikit-learn -> sklearn)
        import_name = pkg.replace("-", "_")
        if pkg == "scikit-learn":
            import_name = "sklearn"
        
        if importlib.util.find_spec(import_name) is None:
            missing.append(pkg)
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print("Run: pip install -r code/requirements.txt")
        return False
    
    print("All required packages are installed.")
    return True

def main():
    """Main entry point for environment setup verification."""
    print("=== Checking Project Environment ===")
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_packages():
        sys.exit(1)
    
    print("Environment check complete.")

if __name__ == "__main__":
    main()
