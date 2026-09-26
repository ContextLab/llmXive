import os
from pathlib import Path

def get_black_config_path() -> Path:
    """Get the path for Black configuration."""
    return Path(__file__).parent.parent / "pyproject.toml"

def get_ruff_config_path() -> Path:
    """Get the path for Ruff configuration."""
    return Path(__file__).parent.parent / "ruff.toml"

def write_config_files() -> None:
    """Write Black and Ruff configuration files."""
    project_root = Path(__file__).parent.parent
    
    # Write Black config to pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    black_config = """[tool.black]
line-length = 88
target-version = ['py38']
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
        
    # Write Ruff config
    ruff_path = project_root / "ruff.toml"
    ruff_config = """# Ruff configuration
line-length = 88
target-version = "py38"

[lint]
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
]

[lint.isort]
known-first-party = ["code"]
"""
    with open(ruff_path, 'w') as f:
        f.write(ruff_config)
        
    print("Linting and formatting configuration files created successfully.")

def main():
    """Main entry point for linting configuration."""
    write_config_files()

if __name__ == "__main__":
    main()