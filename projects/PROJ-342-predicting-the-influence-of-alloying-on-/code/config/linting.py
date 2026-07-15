import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

def get_project_root() -> Path:
    """Return the project root directory (assumed to be the directory containing code/)."""
    current = Path(__file__).resolve()
    # Navigate up to find the root where code/ and .ruff.toml exist
    for parent in current.parents:
        if (parent / "code").exists() and (parent / ".ruff.toml").exists():
            return parent
    # Fallback to current directory if structure not found
    return current.parent.parent

def get_ruff_config_path() -> Path:
    """Return the path to the ruff configuration file."""
    root = get_project_root()
    return root / ".ruff.toml"

def get_black_config_path() -> Path:
    """Return the path to the black configuration file."""
    root = get_project_root()
    return root / "pyproject.toml"

def write_ruff_config() -> None:
    """Write the .ruff.toml file if it doesn't exist."""
    root = get_project_root()
    config_path = root / ".ruff.toml"
    if not config_path.exists():
        content = """[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults (common in ML)
]
extend-per-file-ignores = {}

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        config_path.write_text(content)
        print(f"Created ruff config at {config_path}")

def write_pyproject_black_config() -> None:
    """Ensure pyproject.toml has black configuration."""
    root = get_project_root()
    config_path = root / "pyproject.toml"
    if not config_path.exists():
        content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-metallic-glasses"
version = "0.1.0"
description = "Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses"
requires-python = ">=3.9"
dependencies = [
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "pyyaml>=6.0",
    "requests>=2.31.0",
    "mendeleev==0.31.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
]
optional-dependencies.dev = [
    "ruff>=0.1.0",
    "black>=23.0.0",
    "pytest>=7.4.0",
]

[tool.black]
line-length = 88
target-version = ["py39", "py310", "py311"]
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
extend-exclude = ["__pycache__", "*.egg-info"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
"""
        config_path.write_text(content)
        print(f"Created pyproject.toml with black config at {config_path}")

def run_lint(files: Optional[List[str]] = None) -> int:
    """Run ruff linting on the project or specific files."""
    root = get_project_root()
    config = get_ruff_config_path()
    cmd = [sys.executable, "-m", "ruff", "check", "--config", str(config)]
    if files:
        cmd.extend(files)
    else:
        cmd.append("code")
        cmd.append("tests")
    print(f"Running lint: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root)
    return result.returncode

def run_format(files: Optional[List[str]] = None) -> int:
    """Run black formatting on the project or specific files."""
    root = get_project_root()
    config = get_black_config_path()
    cmd = [sys.executable, "-m", "black", "--config", str(config)]
    if files:
        cmd.extend(files)
    else:
        cmd.append("code")
        cmd.append("tests")
    print(f"Running format: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root)
    return result.returncode

def main() -> None:
    """Main entry point for linting and formatting setup."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup and run linting/formatting")
    parser.add_argument("--init", action="store_true", help="Initialize config files")
    parser.add_argument("--lint", action="store_true", help="Run linter")
    parser.add_argument("--format", action="store_true", help="Run formatter")
    parser.add_argument("files", nargs="*", help="Specific files to process")

    args = parser.parse_args()

    if args.init:
        write_ruff_config()
        write_pyproject_black_config()
        print("Configuration files initialized.")
        sys.exit(0)

    if args.lint:
        exit_code = run_lint(args.files if args.files else None)
        sys.exit(exit_code)

    if args.format:
        exit_code = run_format(args.files if args.files else None)
        sys.exit(exit_code)

    # Default: show help
    parser.print_help()

if __name__ == "__main__":
    main()
