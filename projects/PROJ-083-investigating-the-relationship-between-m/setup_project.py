"""
Project Structure Setup Script for PROJ-083
Creates the directory hierarchy and configuration files required for the
'Investigating the Relationship Between Molecular Topology and Reaction Selectivity'
project.
"""
import os
import sys
from pathlib import Path

# Project root relative to this script (assumed to be at code/ or root)
# We will create the structure relative to the current working directory
PROJECT_ROOT = Path.cwd()
PROJECT_NAME = "PROJ-083-investigating-the-relationship-between-m"

# Define the directory structure to create
# Based on tasks.md and standard project layout
DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/models",
    "code/utils",
    "code/ingestion",
    "code/descriptors",
    "code/modeling",
    "tests/unit",
    "tests/integration",
    "tests/perf",
    "contracts",
    "docs/reports",
    "specs/001-molecular-topology-selectivity",
]

# Define files to create (empty or with minimal boilerplate)
FILES = {
    "data/.gitkeep": "# Raw data storage - do not commit large files",
    "data/processed/.gitkeep": "# Processed data storage",
    "data/models/.gitkeep": "# Model artifacts storage",
    "code/.gitkeep": "# Source code directory",
    "tests/.gitkeep": "# Test directory",
    "contracts/.gitkeep": "# Schema definitions",
    "docs/.gitkeep": "# Documentation",
    "specs/.gitkeep": "# Feature specifications",
    # Configuration placeholders
    "pyproject.toml": """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "proj-083-molecular-topology"
version = "0.1.0"
description = "Investigating the Relationship Between Molecular Topology and Reaction Selectivity"
requires-python = ">=3.11"
dependencies = [
    "rdkit",
    "pandas",
    "scikit-learn",
    "statsmodels",
    "pyyaml",
]

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = []

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
""",
    ".ruff.toml": """# Ruff configuration for PROJ-083
line-length = 88
target-version = "py311"

[lint]
select = [
    "E",  # pycodestyle errors
    "F",  # Pyflakes
    "W",  # pycodestyle warnings
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "SIM",# flake8-simplify
]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided)
fixable = ["ALL"]
unfixable = []

[lint.per-file-ignores]
"__init__.py" = ["F401"]
""",
}

def setup_directories():
    """Create all required directories and files."""
    print(f"Setting up project structure in: {PROJECT_ROOT}")

    # Create directories
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] Created directory: {dir_path}")
        except OSError as e:
            print(f"  [FAIL] Could not create directory {dir_path}: {e}")
            return False

    # Create files
    for file_path, content in FILES.items():
        full_path = PROJECT_ROOT / file_path
        try:
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [OK] Created file: {file_path}")
        except OSError as e:
            print(f"  [FAIL] Could not create file {file_path}: {e}")
            return False

    print("\nProject structure setup complete.")
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)