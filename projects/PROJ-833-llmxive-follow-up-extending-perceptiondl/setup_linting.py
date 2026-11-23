"""
Script to configure linting and formatting tools for the project.
This script installs flake8 and black if missing, and ensures configuration files exist.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_and_install_packages():
    """Check if flake8 and black are installed, install if missing."""
    packages = ['flake8', 'black']
    for package in packages:
        try:
            __import__(package)
            print(f"{package} is already installed.")
        except ImportError:
            print(f"{package} not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def create_flake8_config():
    """Create .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E266, W503
exclude = .git,__pycache__,venv,build,dist,.eggs
per-file-ignores =
    __init__.py:F401
"""
    config_path = Path(".flake8")
    if not config_path.exists():
        config_path.write_text(config_content)
        print(f"Created {config_path}")
    else:
        print(f"{config_path} already exists.")

def create_black_config():
    """Create pyproject.toml Black configuration section if missing."""
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
)/
'''

[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["code", "tests", "specs"]
"""
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            pyproject_path.write_text(content + black_section)
            print(f"Added Black config to {pyproject_path}")
        else:
            print(f"Black config already exists in {pyproject_path}")
    else:
        pyproject_path.write_text(black_section)
        print(f"Created {pyproject_path} with Black config")

def main():
    """Main entry point for setup."""
    print("Setting up linting and formatting tools...")
    check_and_install_packages()
    create_flake8_config()
    create_black_config()
    print("Setup complete.")

if __name__ == "__main__":
    main()