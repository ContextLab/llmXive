"""
Setup script to install linting and formatting tools and create configuration files.
This task implements T003: Configure linting (flake8/black) and formatting tools.
"""
import os
import sys
import subprocess
from pathlib import Path

def install_tools():
    """Install flake8, black, and isort if not already present."""
    tools = ["flake8", "black", "isort"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
            print(f"Successfully installed {tool}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {tool}: {e}")
            return False
    return True

def create_flake8_config():
    """Create .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 120
exclude =
    .git,
    __pycache__,
    data/,
    code/venv,
    build,
    dist
ignore = E203, E266, W503
per-file-ignores =
    # Allow long lines in data files or specific test files if needed
    */tests/*:E501
"""
    config_path = Path(".flake8")
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")

def create_black_config():
    """Create pyproject.toml configuration for Black if not exists, or append."""
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            print("Black configuration already exists in pyproject.toml")
            return True
    
    # Create or update pyproject.toml
    black_config = """[tool.black]
line-length = 120
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
  | data
)/
'''
"""
    
    if pyproject_path.exists():
        with open(pyproject_path, "a") as f:
            f.write("\n" + black_config)
    else:
        with open(pyproject_path, "w") as f:
            f.write(black_config)
    
    print(f"Updated {pyproject_path} with Black configuration")
    return True

def create_isort_config():
    """Create isort configuration in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    
    isort_config = """
[tool.isort]
profile = "black"
line_length = 120
skip_gitignore = true
skip_glob = ["data/*", "code/venv/*", "build/*", "dist/*"]
"""
    
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        if "[tool.isort]" in content:
            print("isort configuration already exists")
            return True
        with open(pyproject_path, "a") as f:
            f.write(isort_config)
    else:
        # Should not happen if create_black_config ran first, but handle gracefully
        with open(pyproject_path, "w") as f:
            f.write(isort_config)
    
    print(f"Updated {pyproject_path} with isort configuration")
    return True

def main():
    """Main entry point for setup_linting."""
    print("Starting linting and formatting setup...")
    
    if not install_tools():
        print("Error: Failed to install linting tools.")
        sys.exit(1)
    
    create_flake8_config()
    create_black_config()
    create_isort_config()
    
    print("\nLinting and formatting tools configured successfully.")
    print("Run 'black . --check' and 'flake8' to verify.")
    return 0

if __name__ == "__main__":
    sys.exit(main())