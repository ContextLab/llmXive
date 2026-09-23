"""
Configure linting (ruff) and formatting (black) tools for the project.

This script ensures that ruff and black are installed in the virtual environment
and creates the necessary configuration files (pyproject.toml) with sensible defaults.
"""
import subprocess
import sys
import os
from pathlib import Path


def ensure_package_installed(package_name: str) -> None:
    """Install a package if it is not already present in the current environment."""
    try:
        __import__(package_name.replace("-", "_"))
    except ImportError:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


def create_ruff_config() -> None:
    """Create a basic ruff.toml configuration file."""
    config_content = """# Ruff configuration
[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    Path("ruff.toml").write_text(config_content)
    print("Created ruff.toml")


def create_pyproject_config() -> None:
    """Create or update pyproject.toml with black configuration."""
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            content += "\n[tool.black]\nline-length = 88\ntarget-version = ['py311']\n"
            pyproject_path.write_text(content)
        else:
            print("pyproject.toml already contains black configuration.")
    else:
        config_content = """[project]
name = "llmXive-statistical-properties"
version = "0.1.0"
description = "Investigating the statistical properties of simulated black hole mergers"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
"""
        pyproject_path.write_text(config_content)
        print("Created pyproject.toml with black configuration.")


def main() -> int:
    """Main entry point for configuring linting and formatting tools."""
    print("Configuring linting and formatting tools...")

    # Ensure packages are installed
    ensure_package_installed("ruff")
    ensure_package_installed("black")

    # Create configuration files
    create_ruff_config()
    create_pyproject_config()

    # Verify installation
    try:
        subprocess.check_call([sys.executable, "-m", "ruff", "--version"])
        subprocess.check_call([sys.executable, "-m", "black", "--version"])
        print("Successfully verified ruff and black installation.")
    except subprocess.CalledProcessError as e:
        print(f"Error verifying tools: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())