"""
Setup script for linting and formatting tools (ruff and black).
"""
import os
import sys
from pathlib import Path
import subprocess

def create_config_files(project_root: Path):
    """Create configuration files for ruff and black."""
    
    # Create pyproject.toml with black configuration
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        black_config = """[tool.black]
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
        with open(pyproject_path, 'w') as f:
            f.write(black_config)
        print(f"Created {pyproject_path}")
    else:
        print(f"{pyproject_path} already exists, skipping creation.")
    
    # Create .ruff.toml with ruff configuration
    ruff_config_path = project_root / ".ruff.toml"
    if not ruff_config_path.exists():
        ruff_config = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
        with open(ruff_config_path, 'w') as f:
            f.write(ruff_config)
        print(f"Created {ruff_config_path}")
    else:
        print(f"{ruff_config_path} already exists, skipping creation.")

def install_dependencies():
    """Install ruff and black if not already installed."""
    tools = ["ruff", "black"]
    
    for tool in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "show", tool],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"{tool} is already installed.")
        except subprocess.CalledProcessError:
            print(f"Installing {tool}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", tool],
                check=True
            )

def main():
    """Main entry point for setup script."""
    project_root = Path(__file__).parent.parent
    
    print("Setting up linting and formatting tools...")
    
    # Install dependencies
    install_dependencies()
    
    # Create configuration files
    create_config_files(project_root)
    
    print("Setup complete!")

if __name__ == "__main__":
    main()