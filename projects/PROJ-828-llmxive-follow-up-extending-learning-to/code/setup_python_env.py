import sys
import subprocess
from pathlib import Path

REQUIRED_PACKAGES = [
    "torch",
    "transformers",
    "datasets",
    "peft",
    "scikit-learn",
    "pandas",
    "numpy",
    "matplotlib",
]

def check_python_version():
    """Ensure Python 3.10+ is used."""
    if sys.version_info < (3, 10):
        print(f"Error: Python 3.10+ required. Found {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"Python version verified: {sys.version}")

def get_requirements_path():
    """Return the path to requirements.txt in the project root."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "requirements.txt"

def create_requirements_file():
    """Create requirements.txt with pinned versions for reproducibility."""
    req_path = get_requirements_path()
    content = (
        "# Core ML/Deep Learning\n"
        "torch>=2.0.0\n"
        "transformers>=4.30.0\n"
        "datasets>=2.14.0\n"
        "peft>=0.5.0\n"
        "\n"
        "# Data Science & Analysis\n"
        "scikit-learn>=1.3.0\n"
        "pandas>=2.0.0\n"
        "numpy>=1.24.0\n"
        "\n"
        "# Visualization\n"
        "matplotlib>=3.7.0\n"
    )
    req_path.write_text(content)
    print(f"Created {req_path}")

def install_dependencies():
    """Install all packages listed in requirements.txt."""
    req_path = get_requirements_path()
    if not req_path.exists():
        create_requirements_file()

    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

def verify_packages():
    """Verify that all required packages are importable."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
            print(f"✓ {pkg} installed")
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} missing")

    if missing:
        print(f"Error: Missing packages: {missing}")
        sys.exit(1)
    print("All required packages verified.")

def main():
    """Main entry point for Python environment setup."""
    check_python_version()
    create_requirements_file()
    install_dependencies()
    verify_packages()

if __name__ == "__main__":
    main()
