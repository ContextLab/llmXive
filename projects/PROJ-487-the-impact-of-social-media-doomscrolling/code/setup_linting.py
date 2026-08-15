import os
import sys
from pathlib import Path
import logging
import subprocess

# Add parent directory to path to allow imports if running as script
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from utils.logging import get_logger

logger = get_logger(__name__)

def create_gitignore_entry():
    """Add Python linting patterns to .gitignore if not present."""
    project_root = Path(__file__).parent.parent
    gitignore_path = project_root / ".gitignore"
    
    patterns = [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".coverage",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".eggs/",
        "*.egg-info/",
        ".venv/",
        "venv/",
        "env/",
        ".env",
    ]
    
    existing_patterns = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_patterns = {line.strip() for line in f if line.strip() and not line.startswith('#')}
    
    new_patterns = [p for p in patterns if p not in existing_patterns]
    
    if new_patterns:
        with open(gitignore_path, 'a') as f:
            f.write("\n# Linting and formatting artifacts\n")
            for pattern in new_patterns:
                f.write(f"{pattern}\n")
        logger.info(f"Added {len(new_patterns)} new patterns to .gitignore")
    else:
        logger.info(".gitignore already contains all necessary linting patterns")

def create_flake8_config():
    """Create a .flake8 configuration file."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / ".flake8"
    
    config_content = """[flake8]
max-line-length = 88
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    *.egg-info,
    data/raw,
    data/processed,
    data/reports,
    .pytest_cache,
    .mypy_cache,
extend-ignore = E203, E501
max-complexity = 10
per-file-ignores =
    # Allow longer lines in test files for fixtures
    tests/*: E501
    # Allow imports in __init__ files
    */__init__.py: F401
"""
    
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    logger.info(f"Created {config_path} with flake8 configuration")

def create_black_config():
    """Create a pyproject.toml file with Black configuration if it doesn't exist, or update it."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | __pycache__
  | build
  | dist
  | \.egg-info
  | data/raw
  | data/processed
  | data/reports
  | \.pytest_cache
  | \.mypy_cache
)/
'''
"""
    
    if not config_path.exists():
        with open(config_path, 'w') as f:
            f.write("[build-system]\nrequires = [\"setuptools>=42\"]\nbuild-backend = \"setuptools.build_meta\"\n")
            f.write(black_section)
        logger.info(f"Created {config_path} with Black configuration")
    else:
        # Check if [tool.black] section exists
        with open(config_path, 'r') as f:
            content = f.read()
        
        if '[tool.black]' in content:
            logger.info(f"{config_path} already contains [tool.black] section. Skipping update.")
        else:
            with open(config_path, 'a') as f:
                f.write(black_section)
            logger.info(f"Added Black configuration to {config_path}")

def create_isort_config():
    """Create a pyproject.toml file with isort configuration if not present."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "pyproject.toml"
    
    isort_section = """
[tool.isort]
profile = "black"
line_length = 88
skip = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    "*.egg-info",
    "data/raw",
    "data/processed",
    "data/reports",
    ".pytest_cache",
    ".mypy_cache",
]
"""
    
    if not config_path.exists():
        with open(config_path, 'w') as f:
            f.write("[build-system]\nrequires = [\"setuptools>=42\"]\nbuild-backend = \"setuptools.build_meta\"\n")
            f.write(isort_section)
        logger.info(f"Created {config_path} with isort configuration")
    else:
        with open(config_path, 'r') as f:
            content = f.read()
        
        if '[tool.isort]' in content:
            logger.info(f"{config_path} already contains [tool.isort] section. Skipping update.")
        else:
            with open(config_path, 'a') as f:
                f.write(isort_section)
            logger.info(f"Added isort configuration to {config_path}")

def install_linting_tools():
    """Install linting and formatting tools if not already installed."""
    tools = [
        "flake8",
        "black",
        "isort",
        "pre-commit",
    ]
    
    logger.info("Checking and installing linting tools...")
    for tool in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", tool], check=True)
            logger.info(f"Successfully ensured {tool} is installed")
        except subprocess.CalledProcessError:
            logger.warning(f"Failed to install {tool}. Please install manually.")

def main():
    """Main entry point for linting setup."""
    logger.info("Starting linting and formatting configuration setup...")
    
    try:
        create_gitignore_entry()
        create_flake8_config()
        create_black_config()
        create_isort_config()
        install_linting_tools()
        
        logger.info("Linting and formatting configuration setup completed successfully.")
        print("\nLinting tools configured:")
        print("  - .flake8: Flake8 linter configuration")
        print("  - pyproject.toml: Black and isort configuration")
        print("  - .gitignore: Updated with linting artifacts")
        print("\nTo run linters:")
        print("  flake8 code/")
        print("  black code/")
        print("  isort code/")
        print("\nTo run pre-commit hooks (if installed):")
        print("  pre-commit install")
        print("  pre-commit run --all-files")
        
        return 0
    except Exception as e:
        logger.error(f"Error during linting setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())