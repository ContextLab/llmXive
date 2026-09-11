"""
Setup script to initialize linting and formatting tools configuration.
This script creates necessary configuration files for ruff and black.
"""
import os
from pathlib import Path

def create_file(filename: str, content: str) -> None:
    """Create a file with the given content."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filename}")

def main():
    """Main function to set up linting configuration."""
    print("Setting up linting and formatting tools...")
    
    # Create .ruff.toml
    ruff_config = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"] # Allow unused imports in __init__.py

[format]
line-length = 88
indent-style = "space"
quote-style = "double"

[lint.isort]
known-first-party = ["ingestion", "modeling", "utils", "setup_dirs", "setup_directories", "setup_env", "setup_linting"]
"""
    create_file("code/.ruff.toml", ruff_config)
    
    # Create pyproject.toml with black settings
    pyproject_config = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "predict-root-architecture"
version = "0.1.0"
description = "Predicting Plant Root Architecture from Soil Nutrient Profiles"
readme = "README.md"
requires-python = ">=3.9"

[tool.black]
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

[tool.ruff]
line-length = 88
target-version = "py39"
src = ["code"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501", "B008"]

[tool.ruff.lint.per-file-ignores]
"code/__init__.py" = ["F401"]
"code/utils/__init__.py" = ["F401"]
"code/ingestion/__init__.py" = ["F401"]
"code/modeling/__init__.py" = ["F401"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
"""
    create_file("code/pyproject.toml", pyproject_config)
    
    print("Linting and formatting tools configured successfully!")
    print("Run 'ruff check code/' to check for issues.")
    print("Run 'black code/' to format code.")

if __name__ == "__main__":
    main()
