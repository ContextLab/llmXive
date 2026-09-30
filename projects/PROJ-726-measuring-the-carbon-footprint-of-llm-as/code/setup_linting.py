"""
Configuration script to initialize Black and Ruff for the project.

This script generates the necessary configuration files (pyproject.toml
and .ruff.toml) and installs the required tools (black, ruff) if not
already present.
"""
import os
import subprocess
import sys
from pathlib import Path


def write_config_file():
    """Write the main configuration to pyproject.toml."""
    pyproject_path = Path("pyproject.toml")

    config_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llm-carbon-footprint"
version = "0.1.0"
description = "Measuring the carbon footprint of LLM-assisted code generation"
requires-python = ">=3.10"
dependencies = [
    "transformers>=4.30.0",
    "codecarbon>=2.0.0",
    "datasets>=2.0.0",
    "scikit-learn>=1.0.0",
    "pandas>=2.0.0",
    "matplotlib>=3.5.0",
    "seaborn>=0.13.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[tool.black]
line-length = 88
target-version = ["py310"]
include = ["code/", "tests/"]
exclude = ["data/"]

[tool.ruff]
# Enable ppep8 (E1-E5, W) and pyflake (F) rules
select = ["E", "F", "W", "I", "N"]
ignore = [
    "E501",  # line too long (handled by black)
    "E722",  # bare except (sometimes needed for robustness)
    "F401",  # unused imports (sometimes needed for type checking)
]
line-length = 88
target-version = "py310"
src = ["code", "tests"]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.mccabe]
max-complexity = 15

[tool.ruff.pyflake]
built-ins = ["__all__"]

[tool.ruff.isort]
known-first-party = ["code", "tests"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["code"]
addopts = "-v --tb=short"
"""

    try:
        with open(pyproject_path, "w") as f:
            f.write(config_content)
        print(f"Successfully wrote configuration to {pyproject_path}")
    except IOError as e:
        print(f"Error writing configuration file: {e}")
        sys.exit(1)


def setup_black_config():
    """Ensure Black is installed and ready."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "black"])
        print("Black is installed.")
    except subprocess.CalledProcessError:
        print("Warning: Could not install Black. Please install manually.")


def setup_ruff_config():
    """Ensure Ruff is installed and ready."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ruff"])
        print("Ruff is installed.")
    except subprocess.CalledProcessError:
        print("Warning: Could not install Ruff. Please install manually.")


def run_format():
    """Run Black to format the codebase."""
    print("Running Black formatter...")
    try:
        subprocess.check_call([sys.executable, "-m", "black", "code/", "tests/"])
        print("Code formatted successfully.")
    except subprocess.CalledProcessError:
        print("Error running Black formatter.")


def run_lint():
    """Run Ruff to lint the codebase."""
    print("Running Ruff linter...")
    try:
        subprocess.check_call([sys.executable, "-m", "ruff", "check", "code/", "tests/"])
        print("Linting completed successfully.")
    except subprocess.CalledProcessError:
        print("Linting found issues (non-zero exit code).")


def main():
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")
    write_config_file()
    setup_black_config()
    setup_ruff_config()
    print("\nConfiguration files created. Run 'python code/setup_linting.py run_format' to format code.")
    print("Run 'python code/setup_linting.py run_lint' to lint code.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "run_format":
            run_format()
        elif sys.argv[1] == "run_lint":
            run_lint()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            sys.exit(1)
    else:
        main()