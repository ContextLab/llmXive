"""
Linting and Formatting Configuration Setup.

This script configures ruff and black for the project, ensuring
consistent code style and quality checks.
"""
import os
import sys
from pathlib import Path
import subprocess
import logging
from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_requirements():
    """Ensure ruff and black are in requirements.txt."""
    requirements_path = Path("code/requirements.txt")
    if not requirements_path.exists():
        logger.warning(f"requirements.txt not found at {requirements_path}. Creating one.")
        requirements_path.parent.mkdir(parents=True, exist_ok=True)
        requirements_path.touch()

    with open(requirements_path, "r") as f:
        content = f.read()

    packages_to_add = ["ruff==0.1.9", "black==23.12.1"]
    updated = False
    for pkg in packages_to_add:
        pkg_name = pkg.split("==")[0]
        if pkg_name not in content:
            logger.info(f"Adding {pkg} to requirements.txt")
            content += f"{pkg}\n"
            updated = True
        else:
            logger.debug(f"{pkg} already in requirements.txt")

    if updated:
        with open(requirements_path, "w") as f:
            f.write(content)
        logger.info(f"Updated {requirements_path}")
    else:
        logger.info("No updates needed for requirements.txt")

def create_ruff_config():
    """Create a ruff.toml configuration file."""
    config_path = Path("ruff.toml")
    if config_path.exists():
        logger.info(f"{config_path} already exists. Skipping creation.")
        return

    config_content = """# Ruff configuration for llmXive project
target-version = "py39"
line-length = 100
indent-width = 4

[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = [
    "E501",   # line too long (handled by black)
    "B008",   # do not perform function calls in argument defaults
    "C901",   # too complex
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["A", "B", "C", "D", "E", "F", "G", "I", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
unfixable = []

# Exclude a few files and directories from linting.
extend-exclude = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "data",
    "reports",
    "build",
    "dist",
]

[lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests

[lint.isort]
known-first-party = ["utils", "01_data_collection", "02_static_analysis", "03_statistical_analysis", "04_reporting"]
force-sort-within-sections = true
combine-as-imports = true

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created {config_path}")

def create_black_config():
    """Create a pyproject.toml section for black if not present."""
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        config_path.touch()

    with open(config_path, "r") as f:
        content = f.read()

    black_section = """
[tool.black]
line-length = 100
target-version = ['py39']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
  | data
  | reports
)/
'''
"""
    if "[tool.black]" not in content:
        content += black_section
        with open(config_path, "w") as f:
            f.write(content)
        logger.info(f"Added [tool.black] section to {config_path}")
    else:
        logger.info(f"[tool.black] already exists in {config_path}")

def main():
    """Main entry point for linting setup."""
    logger.info("Starting linting and formatting configuration setup...")
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    logger.info("Linting and formatting configuration setup complete.")

if __name__ == "__main__":
    main()