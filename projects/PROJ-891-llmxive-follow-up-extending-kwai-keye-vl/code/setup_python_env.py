"""
Setup script to verify Python version and validate environment readiness.
This script ensures the environment is running Python 3.11+ and that
critical dependencies can be imported.
"""
import sys
import subprocess

def main():
    # Check Python version
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ is required. Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✓ Python version check passed: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Verify key dependencies are installed
    required_packages = [
        "opencv",
        "transformers",
        "pandas",
        "numpy",
        "scipy",
        "requests",
        "huggingface_hub",
        "pytest"
    ]

    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg} found")
        except ImportError:
            missing.append(pkg)
            print(f"  ✗ {pkg} missing")

    if missing:
        print(f"\nERROR: Missing required packages: {', '.join(missing)}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

    print("\n✓ Environment setup validation complete.")

if __name__ == "__main__":
    main()