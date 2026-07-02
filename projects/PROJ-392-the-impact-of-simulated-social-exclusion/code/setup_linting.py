"""
Script to configure linting (flake8, black) and formatting tools (isort)
for the project. Creates configuration files and installs dev dependencies.
"""
import subprocess
import sys
import os
from pathlib import Path


def install_dev_dependencies():
    """Install flake8, black, and isort as development dependencies."""
    print("Installing linting and formatting dependencies...")
    packages = ["flake8", "black", "isort", "pyflakes"]
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
    try:
        subprocess.run(cmd, check=True)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False


def create_flake8_config(project_root: Path):
    """Create a .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    .eggs,
    *.egg-info
per-file-ignores =
    # Allow unused imports in __init__.py for public API exposure
    */__init__.py:F401
"""
    config_path = project_root / ".flake8"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Created .flake8 config at {config_path}")


def create_black_config(project_root: Path):
    """Create a pyproject.toml with Black configuration if not exists."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    
    # Check if file exists and has [tool.black]
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml")
            return
        else:
            with open(pyproject_path, "a", encoding="utf-8") as f:
                f.write(black_section)
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write("[project]\nname = \"llmXive-project\"\nversion = \"0.1.0\"\n" + black_section)
    
    print(f"Created/updated Black config in {pyproject_path}")


def create_isort_config(project_root: Path):
    """Create a pyproject.toml section for isort if not exists."""
    pyproject_path = project_root / "pyproject.toml"
    
    isort_section = """
[tool.isort]
profile = "black"
line_length = 88
skip_gitignore = true
known_first_party = ["utils", "data_download", "manipulation", "preprocess", "analysis", "visualization", "pipeline"]
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.isort]" in content:
            print("isort configuration already exists in pyproject.toml")
            return
        else:
            with open(pyproject_path, "a", encoding="utf-8") as f:
                f.write(isort_section)
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write("[project]\nname = \"llmXive-project\"\nversion = \"0.1.0\"\n" + isort_section)
    
    print(f"Created/updated isort config in {pyproject_path}")


def main():
    """Main entry point for setup_linting script."""
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Project root detected at: {project_root}")
    
    if not install_dev_dependencies():
        print("Aborting: dependency installation failed.")
        sys.exit(1)
    
    create_flake8_config(project_root)
    create_black_config(project_root)
    create_isort_config(project_root)
    
    print("\nLinting and formatting tools configured successfully.")
    print("Run 'python code/setup_linting.py' again to re-verify.")
    print("To format code: black code/")
    print("To check linting: flake8 code/")


if __name__ == "__main__":
    main()