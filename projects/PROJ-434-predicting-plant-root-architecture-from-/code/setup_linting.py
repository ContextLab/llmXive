"""
Script to initialize linting and formatting configuration for the project.
This script creates the necessary configuration files for Ruff, Flake8, and Black.
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
    """Main entry point for setting up linting and formatting tools."""
    project_root = Path(__file__).parent

    # Ruff configuration
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
"__init__.py" = ["F401", "F403"]

[format]
line-length = 88
indent-style = "space"
quote-style = "double"
"""
    create_file(project_root / ".ruff.toml", ruff_config)

    # Flake8 configuration
    flake8_config = """[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
"""
    create_file(project_root / ".flake8", flake8_config)

    # Pyproject.toml with Black and Ruff settings
    pyproject_config = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "predict-root-architecture"
version = "0.1.0"
description = "Predicting Plant Root Architecture from Soil Nutrient Profiles"
readme = "README.md"
requires-python = ">=3.8"
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

[tool.ruff]
line-length = 88
target-version = "py38"

[tool.ruff.lint]
select = [
    "E",
    "W",
    "F",
    "I",
    "C",
    "B",
]
ignore = [
    "E501",
    "B008",
    "C901",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
"""
    create_file(project_root / "pyproject.toml", pyproject_config)

    # Create a Makefile for convenience commands
    makefile_content = """# Linting and Formatting Makefile

.PHONY: lint format check-lint check-format fix

# Run Ruff linter
lint:
	ruff check code/

# Run Black formatter
format:
	black code/

# Check linting without fixing
check-lint:
	ruff check code/ --diff

# Check formatting without fixing
check-format:
	black --check code/

# Fix linting issues (where possible)
fix-lint:
	ruff check code/ --fix

# Format and fix linting issues
fix: format fix-lint

# Run all checks
check: check-lint check-format
"""
    create_file(project_root / "Makefile", makefile_content)

    print("\nLinting and formatting configuration completed successfully!")
    print("Run 'make lint' to check code style.")
    print("Run 'make format' to auto-format code.")

if __name__ == "__main__":
    main()