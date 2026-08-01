import os
import sys
from pathlib import Path
import subprocess
import logging
from utils.logger import get_logger

def ensure_requirements():
    """Ensure ruff and black are installed in the current environment."""
    logger = get_logger()
    packages = ["ruff", "black"]
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "show", package], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            logger.info(f"Package '{package}' is already installed.")
        except subprocess.CalledProcessError:
            logger.info(f"Installing '{package}'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    logger.info("Linting and formatting tools verified/installed.")

def create_ruff_config():
    """Create a ruff.toml configuration file in the project root."""
    logger = get_logger()
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["utils", "01_data_collection", "02_static_analysis", "03_statistical_analysis", "04_reporting"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    root = Path(".")
    config_path = root / "ruff.toml"
    if config_path.exists():
        logger.info(f"ruff.toml already exists at {config_path}")
    else:
        config_path.write_text(config_content)
        logger.info(f"Created ruff.toml at {config_path}")

def create_black_config():
    """Create a pyproject.toml section for black configuration."""
    logger = get_logger()
    root = Path(".")
    pyproject_path = root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py39']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # directories
    \.eggs
    | \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | build
    | dist
)/
'''
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            logger.info("Black configuration already exists in pyproject.toml")
            return
        content += black_section
        pyproject_path.write_text(content)
        logger.info("Added Black configuration to pyproject.toml")
    else:
        pyproject_path.write_text(f"[project]\nname = 'llmXive-research'\nversion = '0.1.0'\n{black_section}")
        logger.info("Created pyproject.toml with Black configuration")

def main():
    """Main entry point to configure linting."""
    logger = get_logger()
    logger.info("Starting linting configuration setup...")
    
    try:
        ensure_requirements()
        create_ruff_config()
        create_black_config()
        logger.info("Linting configuration completed successfully.")
    except Exception as e:
        logger.error(f"Failed to configure linting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()