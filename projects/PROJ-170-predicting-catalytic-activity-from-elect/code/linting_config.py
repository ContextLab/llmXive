"""
Linting and Formatting Configuration Management.

This module ensures that the project's linting (ruff) and formatting (black)
configuration files exist and are consistent with project standards.
"""

import os
import sys
from pathlib import Path

from config import get_project_root

# Configuration content literals to ensure idempotent creation
RUFF_CONFIG_CONTENT = """[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = [
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in ML pipelines)
]

# Exclude generated data files and virtual environments
exclude = [
    "data/",
    "outputs/",
    "state/",
    "venv/",
    ".venv/",
    "__pycache__",
]

[lint.per-file-ignores]
# Allow specific style in tests if needed
"tests/*" = ["S101"] # assert statements in tests
"""

BLACK_CONFIG_CONTENT = """[tool.black]
line-length = 88
target-version = ['py310']
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
  | data
  | outputs
  | state
)/
'''
"""

PYPROJECT_EXTRACT = """
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
"""

def ensure_linting_config() -> bool:
    """
    Ensures that .ruff.toml and the relevant [tool.black] section in pyproject.toml exist.
    
    Returns:
        bool: True if configuration is valid or successfully created, False otherwise.
    """
    project_root = get_project_root()
    ruff_config_path = project_root / ".ruff.toml"
    pyproject_path = project_root / "pyproject.toml"
    
    # Ensure .ruff.toml exists
    if not ruff_config_path.exists():
        try:
            with open(ruff_config_path, "w", encoding="utf-8") as f:
                f.write(RUFF_CONFIG_CONTENT)
            print(f"Created {ruff_config_path}")
        except OSError as e:
            print(f"Error creating {ruff_config_path}: {e}", file=sys.stderr)
            return False
    
    # Ensure pyproject.toml exists and contains Black config
    if not pyproject_path.exists():
        try:
            with open(pyproject_path, "w", encoding="utf-8") as f:
                # Basic header + Black + Pytest
                f.write("[build-system]\nrequires = [\"setuptools>=45\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"\n\n[project]\nname = \"llmxive-proj-170\"\nversion = \"0.1.0\"\n")
                f.write("\n")
                f.write(BLACK_CONFIG_CONTENT)
                f.write(PYPROJECT_EXTRACT)
            print(f"Created {pyproject_path}")
        except OSError as e:
            print(f"Error creating {pyproject_path}: {e}", file=sys.stderr)
            return False
    else:
        # Check if Black section exists in existing pyproject.toml
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "[tool.black]" not in content:
                    # Append Black config if missing
                    with open(pyproject_path, "a", encoding="utf-8") as f:
                        f.write("\n" + BLACK_CONFIG_CONTENT)
                    print(f"Appended [tool.black] section to {pyproject_path}")
                else:
                    print(f"{pyproject_path} already contains [tool.black] section.")
        except OSError as e:
            print(f"Error reading {pyproject_path}: {e}", file=sys.stderr)
            return False
    
    return True

def main():
    """CLI entry point for ensuring linting configuration."""
    print("Configuring linting and formatting tools...")
    if ensure_linting_config():
        print("Linting configuration complete.")
        print("To check code: ruff check .")
        print("To format code: black .")
        return 0
    else:
        print("Failed to configure linting tools.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())