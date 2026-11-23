import os
import sys
import subprocess
from pathlib import Path
import json
import logging

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up to find the project root (where code/ directory is)
    while current != current.parent:
        if (current / "code").is_dir() and (current / "data").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root")

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logging.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            cwd=get_project_root()
        )
        if result.stdout:
            logging.info(result.stdout)
        if result.stderr:
            logging.warning(result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"stderr: {e.stderr}")
        raise

def create_ruff_config(project_root: Path) -> None:
    """Create a .ruff.toml configuration file."""
    config_content = """[lint]
# Select common error types
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]

# Ignore specific rules that conflict with project style
ignore = [
    "E501", # line-too-long (handled by black)
    "B008", # do-not-perform-argument-assignment-in-default
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

# Exclude specific directories
extend-exclude = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".venv",
    "venv",
    "env",
    ".eggs",
    "*.egg-info",
]

[lint.per-file-ignores]
# Ignore some rules in test files
"tests/*" = ["S101", "D100", "D101", "D102", "D103"]

[format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces
indent-style = "space"

# Respect magic trailing commas
skip-magic-trailing-comma = false

# Line length (matches black default)
line-length = 88
"""
    config_path = project_root / ".ruff.toml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    logging.info(f"Created {config_path}")

def create_black_config(project_root: Path) -> None:
    """Create a pyproject.toml with black configuration if it doesn't exist."""
    pyproject_path = project_root / "pyproject.toml"
    
    if pyproject_path.exists():
        # Read existing content
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if [tool.black] section already exists
        if "[tool.black]" in content:
            logging.info("Black configuration already exists in pyproject.toml")
            return
        
        # Append black configuration
        black_section = """

[tool.black]
line-length = 88
target-version = ['py311']
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
"""
        with open(pyproject_path, "a", encoding="utf-8") as f:
            f.write(black_section)
        logging.info(f"Appended black configuration to {pyproject_path}")
    else:
        # Create new pyproject.toml with black configuration
        content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "visual-attention-misleading-headlines"
version = "0.1.0"
description = "Impact of visual attention patterns on susceptibility to misleading headlines"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ['py311']
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
"""
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"Created {pyproject_path} with black configuration")

def main() -> int:
    """Main entry point for setting up linting and formatting tools."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        project_root = get_project_root()
        logging.info(f"Project root: {project_root}")
        
        # Create configuration files
        create_ruff_config(project_root)
        create_black_config(project_root)
        
        # Install tools if not present
        logging.info("Checking for ruff installation...")
        try:
            run_command(["pip", "install", "ruff"], check=False)
        except Exception as e:
            logging.warning(f"Could not install ruff: {e}")
        
        logging.info("Checking for black installation...")
        try:
            run_command(["pip", "install", "black"], check=False)
        except Exception as e:
            logging.warning(f"Could not install black: {e}")
        
        logging.info("Linting and formatting configuration complete.")
        return 0
        
    except Exception as e:
        logging.error(f"Failed to set up linting: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())