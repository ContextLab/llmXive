"""
Project initialization script for Python 3.11 environment setup.
Implements T008: Initialize Python 3.11 project.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path


def check_python_version():
    """Verify Python 3.11+ is available."""
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required. Found {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version}")


def create_venv(venv_path="code/.venv"):
    """Create virtual environment if it doesn't exist."""
    venv_dir = Path(venv_path)
    if venv_dir.exists():
        print(f"✓ Virtual environment already exists at {venv_path}")
        return venv_dir

    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_dir, with_pip=True)
    print(f"✓ Virtual environment created")
    return venv_dir


def install_requirements(venv_path="code/.venv"):
    """Install dependencies from requirements.txt."""
    venv_dir = Path(venv_path)
    pip_path = venv_dir / "bin" / "pip" if os.name != "nt" else venv_dir / "Scripts" / "pip.exe"

    if not pip_path.exists():
        print(f"ERROR: pip not found at {pip_path}")
        sys.exit(1)

    requirements_file = Path("code/requirements.txt")
    if not requirements_file.exists():
        print(f"WARNING: requirements.txt not found at {requirements_file}")
        return

    print("Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
    print("✓ Dependencies installed")


def verify_installation():
    """Verify critical packages are importable."""
    critical_packages = ["numpy", "pandas", "yaml", "scipy"]

    for pkg in critical_packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} available")
        except ImportError as e:
            print(f"✗ {pkg} import failed: {e}")
            sys.exit(1)


def main():
    """Main entry point for project setup."""
    print("=" * 60)
    print("Heterogeneous Benchmark - Project Initialization")
    print("=" * 60)

    check_python_version()

    # Create virtual environment
    venv_dir = create_venv()

    # Install requirements
    install_requirements()

    # Verify installation
    verify_installation()

    print("\n" + "=" * 60)
    print("✓ Project initialization complete!")
    print(f"Activate environment: source {venv_dir}/bin/activate")
    print("=" * 60)


if __name__ == "__main__":
    main()
