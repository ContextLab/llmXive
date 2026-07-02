"""
Linting and Formatting Configuration for llmXive Project.

This module provides configuration constants and helper functions for
flake8 and black to ensure consistent code style across the project.
"""

import os
from pathlib import Path

# Project root is assumed to be two levels up from this file's location
# code/ -> project_root/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Black Configuration
BLACK_CONFIG = {
    "line_length": 88,
    "target_version": ["py311"],
    "skip_string_normalization": True,
}

# Flake8 Configuration
FLAKE8_CONFIG = {
    "max-line-length": 88,
    "extend-ignore": "E203, W503",  # E203: whitespace before ':', W503: line break before binary op
    "exclude": [
        ".git",
        "__pycache__",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
        "data",
        "output",
        "figures",
    ],
    "per-file-ignores": {
        "__init__.py": "F401",  # Ignore unused imports in __init__.py
    },
}

def get_black_config_path():
    """Return the path to the pyproject.toml or setup.cfg for Black."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        return pyproject
    return None

def get_flake8_config_path():
    """Return the path to the .flake8 or setup.cfg for Flake8."""
    flake8_cfg = PROJECT_ROOT / ".flake8"
    if flake8_cfg.exists():
        return flake8_cfg
    setup_cfg = PROJECT_ROOT / "setup.cfg"
    if setup_cfg.exists():
        return setup_cfg
    return None

def write_config_files():
    """
    Write configuration files for Black and Flake8 to the project root.
    Creates pyproject.toml for Black and .flake8 for Flake8 if they don't exist.
    """
    # Write Black config to pyproject.toml
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        content = """[tool.black]
line-length = 88
target-version = ['py311']
skip-string-normalization = true
exclude = '''
    (
  /(
      \.eggs
      | \.git
      | \.hg
      | \.mypy_cache
      | \.tox
      | \.venv
      | _build
      | buck-out
      | build
      | dist
  )/
  | /data/
  | /output/
  | /figures/
    )
'''

[tool.flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.eggs,*.egg-info,data,output,figures
per-file-ignores = __init__.py:F401
"""
        pyproject_path.write_text(content)
        print(f"Created {pyproject_path} with linting configuration.")
    else:
        print(f"{pyproject_path} already exists. Skipping creation.")

    # Write .flake8 config
    flake8_path = PROJECT_ROOT / ".flake8"
    if not flake8_path.exists():
        content = f"""[flake8]
max-line-length = {FLAKE8_CONFIG['max-line-length']}
extend-ignore = {FLAKE8_CONFIG['extend-ignore']}
exclude = {','.join(FLAKE8_CONFIG['exclude'])}
per-file-ignores = {list(FLAKE8_CONFIG['per-file-ignores'].items())[0][0]}:{list(FLAKE8_CONFIG['per-file-ignores'].items())[0][1]}
"""
        flake8_path.write_text(content)
        print(f"Created {flake8_path} with linting configuration.")
    else:
        print(f"{flake8_path} already exists. Skipping creation.")


def main():
    """Entry point to generate linting configuration files."""
    write_config_files()
    print("\nLinting and formatting tools configured successfully.")
    print("Run 'black code/' to format code.")
    print("Run 'flake8 code/' to check for linting errors.")


if __name__ == "__main__":
    main()