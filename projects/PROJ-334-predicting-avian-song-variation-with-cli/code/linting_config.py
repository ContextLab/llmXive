import os
from pathlib import Path


def get_black_config_path() -> Path:
    """Return the path to the black configuration file."""
    return Path("pyproject.toml")


def get_ruff_config_path() -> Path:
    """Return the path to the ruff configuration file."""
    return Path("pyproject.toml")


def write_config_files() -> None:
    """
    Write configuration files for black and ruff to pyproject.toml.
    This ensures consistent linting and formatting across the project.
    """
    config_content = """
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = 'code/'
extend-exclude = '''
/(
  # directories
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
  | data
  | tests
)/
'''

[tool.ruff]
line-length = 88
target-version = "py39"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]
exclude = [
    ".eggs",
    ".git",
    ".mypy_cache",
    ".tox",
    ".venv",
    "_build",
    "buck-out",
    "build",
    "dist",
    "data",
    "tests",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["config", "data_setup", "fetch_worldclim", "fetch_xeno_canto", "ingestion", "linting_config", "logging_config", "main", "schema_validator", "setup_dependencies", "setup_dirs", "state_manager", "utils"]
"""
    pyproject_path = Path("pyproject.toml")

    if pyproject_path.exists():
        current_content = pyproject_path.read_text()
        if "[tool.black]" in current_content and "[tool.ruff]" in current_content:
            print("Configuration files already exist and contain black/ruff settings.")
            return
        # Append if they don't exist but file does (simple strategy)
        with open(pyproject_path, "a") as f:
            f.write(config_content)
    else:
        pyproject_path.write_text(config_content)

    print("Successfully wrote black and ruff configurations to pyproject.toml.")


def main() -> None:
    """Main entry point for configuring linting and formatting tools."""
    write_config_files()
    print("Linting and formatting configuration complete.")


if __name__ == "__main__":
    main()