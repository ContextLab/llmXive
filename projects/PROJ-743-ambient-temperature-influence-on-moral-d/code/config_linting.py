"""
Linting and Formatting Configuration Module.

This module provides functions to generate and ensure the existence of
configuration files for Ruff (linting) and Black (formatting), as well
as a pyproject.toml entry for Black settings.
"""

import os
import sys
from pathlib import Path

from config import get_path_env_override


def ensure_pyproject_toml():
    """
    Ensure pyproject.toml exists and contains Black configuration.

    Creates the file if missing, or appends the [tool.black] section
    if it does not already exist.
    """
    root = get_path_env_override("PROJECT_ROOT", Path("."))
    pyproject_path = root / "pyproject.toml"

    black_section = """
[tool.black]
line-length = 88
target-version = ['py39']
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

    if not pyproject_path.exists():
        pyproject_path.write_text(
            "[project]\nname = \"ambient-temp-moral-speed\"\nversion = \"0.1.0\"\n"
            + black_section
        )
        return True

    content = pyproject_path.read_text()
    if "[tool.black]" not in content:
        with open(pyproject_path, "a", encoding="utf-8") as f:
            f.write(black_section)
        return True

    return False


def ensure_ruff_config():
    """
    Ensure .ruff.toml exists with standard linting rules.
    """
    root = get_path_env_override("PROJECT_ROOT", Path("."))
    ruff_path = root / ".ruff.toml"

    config_content = """
# Ruff configuration for ambient-temp-moral-speed
target-version = "py39"
line-length = 88

[lint]
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
]

[lint.isort]
known-first-party = ["code"]
"""

    if not ruff_path.exists():
        ruff_path.write_text(config_content)
        return True
    return False


def ensure_flake8_config():
    """
    Ensure .flake8 exists (legacy fallback, though Ruff is preferred).
    """
    root = get_path_env_override("PROJECT_ROOT", Path("."))
    flake8_path = root / ".flake8"

    config_content = """
[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E501,B008
"""

    if not flake8_path.exists():
        flake8_path.write_text(config_content)
        return True
    return False


def main():
    """
    Main entry point to configure linting and formatting tools.
    """
    print("Configuring linting and formatting tools...")

    created_pyproject = ensure_pyproject_toml()
    created_ruff = ensure_ruff_config()
    created_flake8 = ensure_flake8_config()

    if created_pyproject:
        print("Created/Updated pyproject.toml with Black configuration.")
    if created_ruff:
        print("Created .ruff.toml configuration.")
    if created_flake8:
        print("Created .flake8 configuration (legacy).")

    print("Linting and formatting configuration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())