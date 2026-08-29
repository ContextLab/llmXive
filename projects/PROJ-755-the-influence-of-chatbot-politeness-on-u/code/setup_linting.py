"""
Setup script for linting and formatting tools.
Creates configuration files for ruff, black, and flake8.
"""

import os
import sys
from pathlib import Path
import tomllib
import configparser
import argparse


def check_file_exists(path: Path) -> bool:
    """Check if a file exists."""
    return path.exists()


def validate_ruff_config(config_path: Path) -> bool:
    """Validate ruff configuration file."""
    if not config_path.exists():
        return False
    try:
        # Ruff uses TOML format
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        return "lint" in config or "format" in config
    except Exception:
        return False


def validate_pyproject_black(config_path: Path) -> bool:
    """Validate black configuration in pyproject.toml."""
    if not config_path.exists():
        return False
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        return "tool" in config and "black" in config["tool"]
    except Exception:
        return False


def validate_flake8(config_path: Path) -> bool:
    """Validate flake8 configuration file."""
    if not config_path.exists():
        return False
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        return "flake8" in config
    except Exception:
        return False


def create_ruff_config(base_path: Path) -> None:
    """Create .ruff.toml configuration file."""
    config_content = """[lint]
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
"tests/*" = ["S101"]  # allow assert in tests

[format]
line-length = 88
target-version = "py310"
"""
    config_path = base_path / ".ruff.toml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")


def create_black_config(base_path: Path) -> None:
    """Create black configuration in pyproject.toml."""
    config_path = base_path / "pyproject.toml"
    if not config_path.exists():
        # Create minimal pyproject.toml if it doesn't exist
        config_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-proj-755"
version = "0.1.0"
description = "Influence of Chatbot Politeness on User-Perceived Quality"
requires-python = ">=3.10"
dependencies = [
    "transformers",
    "datasets",
    "statsmodels",
    "pandas",
    "scikit-learn",
    "numpy",
    "pyyaml",
    "tqdm",
    "rpy2",
    "textstat",
    "evalue",
    "torch",
    "python-dotenv",
    "pyarrow",
    "tomli",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "pytest>=7.0.0",
]

[tool.black]
line-length = 88
target-version = ["py310"]
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
)/
'''

[tool.ruff]
line-length = 88
target-version = "py310"
src = ["code", "tests"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4"]
ignore = ["E501", "B008"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["code"]
"""
        with open(config_path, "w") as f:
            f.write(config_content)
        print(f"Created {config_path} with Black configuration")
    else:
        # Append or update black config
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
            if "tool" not in config:
                config["tool"] = {}
            config["tool"]["black"] = {
                "line-length": 88,
                "target-version": ["py310"],
            }
            with open(config_path, "w") as f:
                import tomli_w
                tomli_w.dump(config, f)
            print(f"Updated {config_path} with Black configuration")
        except Exception as e:
            print(f"Warning: Could not update pyproject.toml: {e}")


def create_flake8_config(base_path: Path) -> None:
    """Create .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    data
max-complexity = 10
"""
    config_path = base_path / ".flake8"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")


def install_linting_tools() -> None:
    """Print instructions for installing linting tools."""
    print("\nLinting tools configuration complete.")
    print("To install the tools, run:")
    print("  pip install ruff black flake8 pytest")
    print("\nTo format code with Black:")
    print("  black code/ tests/")
    print("\nTo lint with Ruff:")
    print("  ruff check code/ tests/")
    print("\nTo lint with Flake8:")
    print("  flake8 code/ tests/")


def main() -> None:
    """Main entry point for setup_linting."""
    parser = argparse.ArgumentParser(
        description="Setup linting and formatting tools"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration files",
    )
    args = parser.parse_args()

    base_path = Path(__file__).resolve().parent.parent

    print("Setting up linting and formatting tools...")

    # Create ruff config
    ruff_path = base_path / ".ruff.toml"
    if args.force or not check_file_exists(ruff_path):
        create_ruff_config(base_path)
    else:
        if validate_ruff_config(ruff_path):
            print(f"{ruff_path} already exists and is valid.")
        else:
            create_ruff_config(base_path)

    # Create black config in pyproject.toml
    pyproject_path = base_path / "pyproject.toml"
    if args.force or not check_file_exists(pyproject_path):
        create_black_config(base_path)
    else:
        if validate_pyproject_black(pyproject_path):
            print(f"{pyproject_path} already has Black configuration.")
        else:
            create_black_config(base_path)

    # Create flake8 config
    flake8_path = base_path / ".flake8"
    if args.force or not check_file_exists(flake8_path):
        create_flake8_config(base_path)
    else:
        if validate_flake8(flake8_path):
            print(f"{flake8_path} already exists and is valid.")
        else:
            create_flake8_config(base_path)

    install_linting_tools()


if __name__ == "__main__":
    main()