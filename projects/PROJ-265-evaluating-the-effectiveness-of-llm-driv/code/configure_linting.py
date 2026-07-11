import os
import sys
from pathlib import Path

def create_pyproject_toml(root: Path) -> None:
    """Create or update pyproject.toml with black and ruff configuration."""
    content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
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

[tool.ruff]
target-version = "py311"
line-length = 88
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
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "*.egg-info",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""
    file_path = root / "pyproject.toml"
    write_config_file(file_path, content)

def create_ruff_toml(root: Path) -> None:
    """Create .ruff.toml as an alternative config if preferred."""
    # Note: pyproject.toml is preferred, but providing .ruff.toml for flexibility
    content = """[lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C901"]
exclude = [".git", ".venv", "__pycache__", "build", "dist", "*.egg-info"]
target-version = "py311"

[format]
line-length = 88
"""
    file_path = root / ".ruff.toml"
    write_config_file(file_path, content)

def create_pre_commit_config(root: Path) -> None:
    """Create .pre-commit-config.yaml for automated linting/formatting."""
    content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix]
- id: ruff-format
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
- id: black
  language_version: python3.11
"""
    file_path = root / ".pre-commit-config.yaml"
    write_config_file(file_path, content)

def write_config_file(file_path: Path, content: str) -> None:
    """Write content to file if it doesn't exist or differs."""
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            existing = f.read()
        if existing == content:
            print(f"Skipping {file_path}: no changes.")
            return
        print(f"Updating {file_path}.")
    else:
        print(f"Creating {file_path}.")
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main() -> None:
    """Main entry point to configure linting and formatting tools."""
    root = Path.cwd()
    print(f"Configuring linting and formatting tools in {root}...")
    
    create_pyproject_toml(root)
    create_ruff_toml(root)
    create_pre_commit_config(root)
    
    print("Configuration complete. Run 'pip install -r requirements.txt' and 'pre-commit install' to activate.")

if __name__ == "__main__":
    main()