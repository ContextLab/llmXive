"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script ensures configuration files are present in the code/ directory.
"""
import os
from pathlib import Path

def create_ruff_config():
    """Create .ruff.toml configuration file."""
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    path = Path("code/.ruff.toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config_content)
    print(f"Created {path}")

def create_black_config():
    """Create .black.toml configuration file."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
    path = Path("code/.black.toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config_content)
    print(f"Created {path}")

def main():
    """Run setup for linting and formatting tools."""
    print("Configuring linting (ruff) and formatting (black)...")
    create_ruff_config()
    create_black_config()
    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()
