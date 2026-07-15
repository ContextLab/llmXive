"""
Script to configure linting and formatting tools for the project.
This script installs the necessary tools (flake8, black) and generates
configuration files (.flake8, pyproject.toml for black) in the project root.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_and_install_packages():
    """Check if flake8 and black are installed, install if missing."""
    packages = {
        "flake8": "flake8",
        "black": "black"
    }

    for module, package in packages.items():
        try:
            __import__(module)
            print(f"✓ {module} is already installed.")
        except ImportError:
            print(f"⚠ {module} is not installed. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} installed successfully.")
            except subprocess.CalledProcessError:
                print(f"✗ Failed to install {package}. Please install manually.")
                sys.exit(1)

def create_flake8_config():
    """Create .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E501
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
"""
    config_path = Path(".flake8")
    if not config_path.exists():
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"✓ Created {config_path}")
    else:
        print(f"⚠ {config_path} already exists. Skipping.")

def create_black_config():
    """Create pyproject.toml section for Black if not present."""
    pyproject_path = Path("pyproject.toml")
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
  | \\*.egg-info
)/
'''
"""

    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            print(f"⚠ Black configuration already exists in {pyproject_path}. Skipping.")
            return
        with open(pyproject_path, "a") as f:
            f.write(black_section)
        print(f"✓ Appended Black configuration to {pyproject_path}")
    else:
        with open(pyproject_path, "w") as f:
            f.write("[build-system]\nrequires = [\"setuptools>=42\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"\n")
            f.write(black_section)
        print(f"✓ Created {pyproject_path} with Black configuration")

def main():
    """Main entry point."""
    print("Starting linting and formatting configuration...")
    
    # Ensure we are in the project root
    # The script is expected to be run from the project root or the project root path is passed
    # For this task, we assume the script runs from the project root relative to the repo
    # Since the task says "in projects/.../", we assume the script is run from there or we target that dir
    # However, standard practice is to run config scripts from the root.
    # We will assume the current working directory is the project root where T001 created structure.
    
    check_and_install_packages()
    create_flake8_config()
    create_black_config()
    
    print("\nLinting and formatting configuration complete.")
    print("You can now run:")
    print("  black . --check")
    print("  flake8")

if __name__ == "__main__":
    main()