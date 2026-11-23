"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script ensures dependencies are installed and configuration files exist.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_dependencies():
    """Ensure ruff and black are installed in the current environment."""
    print("Checking for required linting/formatting tools...")
    tools = [
        ("ruff", "ruff"),
        ("black", "black"),
    ]
    
    missing = []
    for name, cmd in tools:
        try:
            subprocess.run([cmd, "--version"], check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  ✓ {name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(name)
            print(f"  ✗ {name} is missing")

    if missing:
        print(f"\nInstalling missing tools: {', '.join(missing)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
            print("Installation successful.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies: {e}")
            sys.exit(1)

def create_pyproject_config():
    """Ensure pyproject.toml exists with Black and Ruff configuration."""
    root = Path(__file__).parent
    config_file = root / "pyproject.toml"
    
    if not config_file.exists():
        print(f"Creating {config_file} with tool configurations...")
        content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "statistical-poll-aggregation"
version = "0.1.0"
description = "Statistical Analysis of Publicly Available Election Poll Aggregates"
requires-python = ">=3.9"
dependencies = [
    "pandas",
    "numpy",
    "scipy",
    "pymc",
    "arviz",
    "requests",
    "pyyaml",
    "statsmodels",
    "pytest",
    "ruff",
    "black",
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
target-version = "py39"
src = ["code", "src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4"]
ignore = ["E501", "B008"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401", "F403"]
"tests/*" = ["S101", "D100", "D103"]
"""
        config_file.write_text(content)
        print(f"Created {config_file}")
    else:
        print(f"{config_file} already exists.")

def create_ruff_config():
    """Ensure .ruff.toml exists for Ruff configuration."""
    root = Path(__file__).parent
    config_file = root / ".ruff.toml"
    
    if not config_file.exists():
        print(f"Creating {config_file}...")
        content = """[lint]
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
]

[lint.per-file-ignores]
"__init__.py" = ["F401", "F403"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

[isort]
known-first-party = ["src", "code", "tests"]
force-single-line = false
"""
        config_file.write_text(content)
        print(f"Created {config_file}")
    else:
        print(f"{config_file} already exists.")

def main():
    """Main entry point for linting setup."""
    print("=== Setting up Linting and Formatting Tools ===")
    ensure_dependencies()
    create_pyproject_config()
    create_ruff_config()
    print("=== Setup Complete ===")
    print("\nTo run Black: black .")
    print("To run Ruff: ruff check .")
    print("To format and lint: black . && ruff check .")

if __name__ == "__main__":
    main()