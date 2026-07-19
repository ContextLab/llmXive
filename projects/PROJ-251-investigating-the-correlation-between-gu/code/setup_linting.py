"""
Setup script for linting and formatting tools.
This script ensures configuration files for Ruff and Black exist in the code/ directory.
"""
import os
from pathlib import Path

def create_config_files():
    """Create .ruff.toml and pyproject.toml if they do not exist."""
    base_dir = Path(__file__).parent

    ruff_config = base_dir / ".ruff.toml"
    pyproject = base_dir / "pyproject.toml"

    # Ruff configuration content
    ruff_content = """[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "ANN101", # Missing type annotation for `self` in method
    "ANN102", # Missing type annotation for `cls` in classmethod
    "E501",   # Line too long (handled by black)
]
target-version = "py311"

[lint.isort]
known-first-party = ["utils", "tests"]
force-sort-within-sections = true

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""

    # PyProject configuration content (for Black and build system)
    pyproject_content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-gut-immune"
version = "0.1.0"
description = "Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "scikit-learn>=1.2.0",
    "pyyaml>=6.0",
    "requests>=2.28.0",
    "biom-format>=2.1.14",
    "datasets>=2.14.0",
    "python-dotenv>=1.0.0",
    "psutil>=5.9.0",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
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
line-length = 88
target-version = "py311"
extend-exclude = ["__pycache__", ".venv"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["utils", "tests"]
"""

    if not ruff_config.exists():
        with open(ruff_config, "w", encoding="utf-8") as f:
            f.write(ruff_content)
        print(f"Created: {ruff_config}")
    else:
        print(f"Exists: {ruff_config}")

    if not pyproject.exists():
        with open(pyproject, "w", encoding="utf-8") as f:
            f.write(pyproject_content)
        print(f"Created: {pyproject}")
    else:
        print(f"Exists: {pyproject}")

    print("Linting and formatting configuration setup complete.")

if __name__ == "__main__":
    create_config_files()
