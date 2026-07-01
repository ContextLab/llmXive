import os
import subprocess
import sys
from pathlib import Path
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_tools():
    """Install ruff and black into the current environment."""
    logger.info("Installing linting and formatting tools (ruff, black)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        logger.info("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install tools: {e}")
        raise

def create_ruff_config():
    """Create a default ruff configuration file (pyproject.toml)."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    ruff_config_content = """[tool.ruff]
# Select specific rules (or use 'ALL' for comprehensive checking)
select = ["E", "W", "F", "I", "N", "B", "C4", "UP"]
ignore = []

# Allow autofix for all enabled rules (when applicable)
fixable = ["ALL"]
unfixable = []

# Exclude a few specific files/directories
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
]

# Same as Black
line-length = 88

# Allow unused variables when underscore-prefixed
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

target-version = "py311"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.ruff.isort]
known-first-party = ["data", "models", "analysis", "tests", "tools"]
"""

    if pyproject_path.exists():
        logger.info(f"Updating existing {pyproject_path} with ruff config...")
        # Simple append or overwrite strategy for this task
        with open(pyproject_path, 'w') as f:
            f.write(ruff_config_content)
    else:
        logger.info(f"Creating new {pyproject_path} with ruff config...")
        with open(pyproject_path, 'w') as f:
            f.write(ruff_config_content)

    logger.info("Ruff configuration created/updated in pyproject.toml.")

def create_black_config():
    """Create a default black configuration (usually in pyproject.toml as well)."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    # Since we are writing to pyproject.toml for ruff, we ensure black config is there too.
    # We will read existing, append if missing, or write if new.
    
    black_config_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.nox
  | \.pants.d
  | \.pytype
  | \.ruff_cache
  | \.svn
  | \.tox
  | \.venv
  | __pypackages__
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    
    if pyproject_path.exists():
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        if "[tool.black]" not in content:
            logger.info(f"Appending black config to {pyproject_path}...")
            with open(pyproject_path, 'a') as f:
                f.write(black_config_section)
        else:
            logger.info(f"Black config already present in {pyproject_path}.")
    else:
        # This case should be handled by create_ruff_config usually, but safe fallback
        logger.info(f"Creating new {pyproject_path} with black config...")
        with open(pyproject_path, 'w') as f:
            f.write(black_config_section)

    logger.info("Black configuration ensured in pyproject.toml.")

def main():
    """Main entry point to configure linting and formatting tools."""
    logger.info("Starting linting and formatting configuration setup...")
    try:
        install_tools()
        create_ruff_config()
        create_black_config()
        logger.info("Linting and formatting configuration setup complete.")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()