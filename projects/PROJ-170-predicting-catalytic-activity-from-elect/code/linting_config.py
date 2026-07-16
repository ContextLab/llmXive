"""
Linting and Formatting Configuration Manager.

This module ensures that configuration files for Ruff (linting) and Black (formatting)
exist in the project root. It generates standard configurations compatible with the
project's requirements (Python 3.10+).
"""
import os
import sys
from pathlib import Path

from config import get_project_root


def ensure_linting_config() -> None:
    """
    Create or verify the existence of linting and formatting configuration files.

    Creates:
    - pyproject.toml: Contains [tool.black] and [tool.ruff] sections.
    - .flake8: Legacy configuration (optional, but good for compatibility).

    If the files exist, this function checks for the presence of the required
    sections and updates them if necessary (idempotent behavior).
    """
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    flake8_path = project_root / ".flake8"

    # Ensure pyproject.toml exists
    if not pyproject_path.exists():
        pyproject_path.touch()

    content = pyproject_path.read_text()

    # Define Black configuration
    black_section = """
[tool.black]
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
)/
'''
"""

    # Define Ruff configuration
    ruff_section = """
[tool.ruff]
target-version = "py310"
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
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in fastapi/some ML libs)
]
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"] # Ignore unused imports in __init__.py files
"""

    # Simple injection logic to ensure sections exist
    # In a real robust system, we would use tomlkit to parse/modify,
    # but for a setup script, string injection is sufficient.

    if "[tool.black]" not in content:
        content += black_section
        pyproject_path.write_text(content)
        print(f"Added [tool.black] configuration to {pyproject_path}")

    if "[tool.ruff]" not in content:
        content += ruff_section
        pyproject_path.write_text(content)
        print(f"Added [tool.ruff] configuration to {pyproject_path}")

    # Create .flake8 for legacy tool compatibility
    flake8_content = """
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
"""
    if not flake8_path.exists():
        flake8_path.write_text(flake8_content)
        print(f"Created {flake8_path}")
    else:
        # Check if max-line-length is set, update if not
        current = flake8_path.read_text()
        if "max-line-length" not in current:
            flake8_path.write_text(flake8_content + "\n" + current)
            print(f"Updated {flake8_path}")


def main() -> None:
    """Entry point for CLI execution."""
    print("Configuring linting and formatting tools...")
    ensure_linting_config()
    print("Linting and formatting configuration complete.")


if __name__ == "__main__":
    main()