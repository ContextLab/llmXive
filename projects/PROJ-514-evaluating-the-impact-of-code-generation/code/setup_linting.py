import os
import sys
from pathlib import Path
import subprocess
import logging

# Ensure we can import from the code directory
code_root = Path(__file__).resolve().parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logger import get_logger

logger = get_logger(__name__)

def ensure_requirements():
    """
    Ensures ruff and black are present in the current environment.
    If not, attempts to install them via pip.
    """
    required_packages = ["ruff", "black"]
    installed = []
    missing = []

    for package in required_packages:
        try:
            __import__(package)
            installed.append(package)
        except ImportError:
            missing.append(package)

    if missing:
        logger.info(f"Missing packages detected: {missing}. Attempting installation...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            logger.info(f"Successfully installed: {missing}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install missing packages: {e}")
            return False
    
    logger.info(f"All required linting tools are installed: {installed}")
    return True

def create_ruff_config():
    """
    Creates a .ruff.toml configuration file in the project root
    with settings appropriate for this research project.
    """
    project_root = code_root.parent
    config_path = project_root / ".ruff.toml"

    if config_path.exists():
        logger.info(f"Ruff config already exists at {config_path}")
        return

    config_content = """
    [lint]
    select = [
        "E",  # pycodestyle errors
        "W",  # pycodestyle warnings
        "F",  # Pyflakes
        "I",  # isort
        "C",  # flake8-comprehensions
        "B",  # flake8-bugbear
        "UP", # pyupgrade
        "ANN",# flake8-annotations (strict mode optional, keeping basic for now)
    ]
    ignore = [
        "E501", # line too long (handled by black)
        "B008", # do not perform function calls in argument defaults (common in research scripts)
        "ANN101", # missing type annotation for self in method
        "ANN102", # missing type annotation for cls in classmethod
    ]
    target-version = "py39"

    [lint.isort]
    known-first-party = ["utils", "01_data_collection", "02_static_analysis", "03_statistical_analysis", "04_reporting"]

    [format]
    quote-style = "double"
    indent-style = "space"
    skip-magic-trailing-comma = false
    line-ending = "auto"
    """
    
    with open(config_path, "w") as f:
        f.write(config_content)
    
    logger.info(f"Created Ruff configuration at {config_path}")

def create_black_config():
    """
    Creates a pyproject.toml section for Black configuration
    if it doesn't already exist, or creates a standalone .black.toml 
    if preferred (using pyproject.toml is standard).
    """
    project_root = code_root.parent
    pyproject_path = project_root / "pyproject.toml"

    # Check if [tool.black] section exists
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
            if "[tool.black]" in content:
                logger.info("Black configuration already exists in pyproject.toml")
                return

    # Append configuration to pyproject.toml
    black_config = """
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
        with open(pyproject_path, "a") as f:
            f.write(black_config)
    else:
        with open(pyproject_path, "w") as f:
            f.write(black_config)
    
    logger.info(f"Updated Black configuration in {pyproject_path}")

def main():
    """
    Main entry point for configuring linting tools.
    """
    logger.info("Starting linting configuration setup...")
    
    if not ensure_requirements():
        logger.error("Setup failed due to missing dependencies.")
        sys.exit(1)
    
    create_ruff_config()
    create_black_config()
    
    logger.info("Linting configuration completed successfully.")
    print("Linting tools (ruff, black) configured successfully.")

if __name__ == "__main__":
    main()