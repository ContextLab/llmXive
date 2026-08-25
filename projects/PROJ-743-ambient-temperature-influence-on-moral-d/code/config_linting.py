"""
Configuration module for linting and formatting tools.
Ensures that ruff, flake8, and black configurations are present in the project.
"""

import os
import sys
from pathlib import Path
from config import get_path_env_override


def ensure_pyproject_toml() -> bool:
    """
    Ensure pyproject.toml exists with basic black and ruff configuration.
    Returns True if the file was created or already existed with content.
    """
    root = get_path_env_override()
    pyproject_path = root / "pyproject.toml"

    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content or "[tool.ruff]" in content:
            return True

    # Create or append basic configuration
    config_content = """
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

[tool.ruff]
line-length = 88
target-version = "py39"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""
    with open(pyproject_path, "w") as f:
        f.write(config_content)

    return True


def ensure_ruff_config() -> bool:
    """
    Ensure ruff configuration is present (usually in pyproject.toml).
    This function primarily validates that the pyproject.toml has ruff settings.
    """
    root = get_path_env_override()
    pyproject_path = root / "pyproject.toml"

    if not pyproject_path.exists():
        ensure_pyproject_toml()

    content = pyproject_path.read_text()
    return "[tool.ruff]" in content


def ensure_flake8_config() -> bool:
    """
    Ensure .flake8 or setup.cfg contains flake8 configuration.
    Returns True if configuration exists.
    """
    root = get_path_env_override()
    flake8_path = root / ".flake8"
    setup_cfg_path = root / "setup.cfg"

    # Prefer .flake8 if it exists
    if flake8_path.exists():
        return True

    # Check setup.cfg
    if setup_cfg_path.exists():
        content = setup_cfg_path.read_text()
        if "[flake8]" in content:
            return True

    # Create .flake8
    config_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E501,W503
max-complexity = 10
"""
    with open(flake8_path, "w") as f:
        f.write(config_content)

    return True


def main() -> None:
    """
    Main entry point to configure linting and formatting tools.
    """
    print("Configuring linting and formatting tools...")

    try:
        ensure_pyproject_toml()
        print("✓ pyproject.toml configured")

        if ensure_ruff_config():
            print("✓ Ruff configuration verified")

        if ensure_flake8_config():
            print("✓ Flake8 configuration verified")

        print("\nLinting and formatting configuration complete.")
        print("\nYou can now run:")
        print("  black code/ --check")
        print("  ruff check code/")
        print("  flake8 code/")

    except Exception as e:
        print(f"Error configuring linting tools: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()