"""
Script to initialize linting and formatting configuration files.
This script creates the necessary configuration files for Ruff and Black.
"""
import os
from pathlib import Path

def create_file(path: Path, content: str) -> None:
    """Create a file with the given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {path}")

def main() -> None:
    """Main entry point to create linting configuration files."""
    project_root = Path(__file__).parent

    # Create .ruff.toml
    ruff_config = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assertions in tests

[format]
line-length = 88
indent-style = "space"
quote-style = "double"
"""
    create_file(project_root / ".ruff.toml", ruff_config)

    # Create pyproject.toml with Black and Ruff settings
    pyproject_config = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "predict-root-architecture"
version = "0.1.0"
description = "Predicting Plant Root Architecture from Soil Nutrient Profiles"
requires-python = ">=3.9"
dependencies = [
    "scikit-learn",
    "pandas",
    "numpy",
    "rasterio",
    "geopandas",
    "requests",
    "pyyaml",
    "pytest",
    "ruff",
    "black",
    "python-dotenv",
]

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
src = ["code", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
"""
    create_file(project_root / "pyproject.toml", pyproject_config)

    print("\nLinting and formatting configuration created successfully.")
    print("To format code: black code/ tests/")
    print("To lint code: ruff check code/ tests/")

if __name__ == "__main__":
    main()