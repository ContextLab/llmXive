"""
Script to configure linting (flake8) and formatting (black) tools for the project.
This script installs the tools if missing and generates configuration files.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_and_install_packages():
    """Check if flake8 and black are installed, install if missing."""
    packages = ["flake8", "black"]
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} is already installed.")
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            print(f"✓ {pkg} installed successfully.")

def create_flake8_config(project_root: Path):
    """Create a .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E266, W503
exclude = .git,__pycache__,build,dist,venv,.venv
per-file-ignores =
    */__init__.py:F401
"""
    config_path = project_root / ".flake8"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"✓ Created {config_path}")

def create_black_config(project_root: Path):
    """Create a pyproject.toml with Black configuration if not exists or update it."""
    toml_path = project_root / "pyproject.toml"
    
    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
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
"""
    
    if toml_path.exists():
        # Append black config if not present
        with open(toml_path, "r") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(toml_path, "a") as f:
                f.write(black_config)
            print(f"✓ Updated {toml_path} with Black configuration.")
        else:
            print(f"✓ Black configuration already exists in {toml_path}.")
    else:
        # Create new file with minimal build system and black config
        minimal_toml = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-follow-up-extending-perceptiondl"
version = "0.1.0"
description = "Extending PerceptionDLM Parallel Region Perception"
requires-python = ">=3.11"
dependencies = [
    "torch",
    "transformers",
    "diffusers",
    "spacy",
    "pandas",
    "scikit-learn",
    "matplotlib",
    "datasets",
    "huggingface_hub",
    "psutil",
    "flake8",
    "black",
    "jsonschema",
    "pyyaml",
    "pillow",
    "numpy",
]
"""
        with open(toml_path, "w") as f:
            f.write(minimal_toml + black_config)
        print(f"✓ Created {toml_path} with Black configuration.")

def main():
    """Main entry point for setting up linting and formatting."""
    # Determine project root (assuming script is in code/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print(f"Setting up linting and formatting in: {project_root}")
    
    # 1. Check and install packages
    check_and_install_packages()

    # 2. Create .flake8 config
    create_flake8_config(project_root)

    # 3. Create/Update pyproject.toml for Black
    create_black_config(project_root)

    print("\n✓ Linting (flake8) and Formatting (black) setup complete.")
    print("Run 'flake8 .' to check for linting errors.")
    print("Run 'black .' to format code.")

if __name__ == "__main__":
    main()