"""
Setup script for linting (ruff) and formatting (black) tools.
This script installs the tools and generates configuration files.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Install ruff and black, and create configuration files."""
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)

    print("Installing linting and formatting tools...")
    # Install ruff and black
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
    except subprocess.CalledProcessError:
        print("Failed to install ruff or black. Please install manually.")
        return 1

    # Create ruff.toml configuration
    ruff_config = config_dir / "ruff.toml"
    if not ruff_config.exists():
        ruff_content = """
# Ruff configuration for llmXive project
target-version = "py311"
line-length = 88

[lint]
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
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[lint.isort]
known-first-party = ["src", "tests"]
"""
        ruff_config.write_text(ruff_content.strip())
        print(f"Created {ruff_config}")
    else:
        print(f"{ruff_config} already exists, skipping.")

    # Create pyproject.toml for Black if it doesn't exist
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        black_content = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
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
"""
        pyproject.write_text(black_content.strip())
        print(f"Created {pyproject} for Black configuration")
    else:
        print(f"{pyproject} already exists, skipping.")

    print("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())