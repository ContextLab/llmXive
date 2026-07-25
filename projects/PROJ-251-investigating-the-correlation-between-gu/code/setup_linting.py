"""
Setup script for linting and formatting tools (ruff, black).
"""
import os
import sys
from pathlib import Path
import subprocess

def create_config_files(project_root: Path):
    """
    Create configuration files for ruff and black.
    """
    # Create pyproject.toml with black and ruff config if it doesn't exist
    pyproject_path = project_root / "pyproject.toml"
    
    black_config = """
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
"""
    
    ruff_config = """
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"""
    
    if not pyproject_path.exists():
        with open(pyproject_path, "w") as f:
            f.write(black_config + "\n" + ruff_config)
        print(f"Created {pyproject_path}")
    else:
        print(f"{pyproject_path} already exists. Skipping creation.")

def install_dependencies():
    """
    Install ruff and black if not already installed.
    """
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", tool], check=True)
            print(f"{tool} installed/verified.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {tool}. Please install manually.")

def main():
    """
    Main entry point for setup_linting.
    """
    project_root = Path.cwd()
    
    print("Setting up linting and formatting tools...")
    
    # Install tools
    install_dependencies()
    
    # Create config files
    create_config_files(project_root)
    
    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()