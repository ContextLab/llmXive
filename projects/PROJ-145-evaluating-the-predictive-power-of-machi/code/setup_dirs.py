"""
Project Initialization Script for llmXive HEA Predictive Power Pipeline.

This script creates the required directory structure and initializes
Python packages with __init__.py files. It also generates configuration
files for linting (ruff) and formatting (black).
"""
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory(path: Path) -> None:
    """Create a directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    else:
        logger.info(f"Directory already exists: {path}")

def create_init_file(path: Path) -> None:
    """Create an empty __init__.py file in the given directory."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        logger.info(f"Created __init__.py in: {path}")
    else:
        logger.info(f"__init__.py already exists in: {path}")

def create_config_files() -> None:
    """Create configuration files for ruff and black."""
    root = Path(__file__).parent.parent

    # Create .ruff.toml
    ruff_config = root / ".ruff.toml"
    if not ruff_config.exists():
        ruff_config.write_text("""
# Ruff configuration
line-length = 88
target-version = "py39"

[lint]
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
]

[lint.isort]
known-first-party = ["code"]
""")
        logger.info("Created .ruff.toml")
    else:
        logger.info(".ruff.toml already exists")

    # Create pyproject.toml (if not exists)
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        pyproject.write_text("""
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
""")
        logger.info("Created pyproject.toml")
    else:
        logger.info("pyproject.toml already exists")

def main() -> None:
    """Main function to initialize the project structure."""
    root = Path(__file__).parent.parent

    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests/unit",
        "tests/integration",
        "specs",
    ]

    logger.info("Starting project initialization...")

    # Create directories
    for dir_path in directories:
        full_path = root / dir_path
        create_directory(full_path)

    # Create __init__.py files in all directories
    for dir_path in directories:
        full_path = root / dir_path
        create_init_file(full_path)

    # Create configuration files
    create_config_files()

    logger.info("Project initialization completed successfully.")

if __name__ == "__main__":
    main()