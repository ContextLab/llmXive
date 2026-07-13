import os
import subprocess
import sys
from pathlib import Path
import logging

def install_dev_dependencies():
    """Install ruff and black as development dependencies."""
    logger = logging.getLogger(__name__)
    logger.info("Installing linting and formatting tools (ruff, black)...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "ruff", "black", "--quiet"
        ])
        logger.info("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        raise

def create_config_files():
    """Create ruff.toml and pyproject.toml configuration files."""
    logger = logging.getLogger(__name__)
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    # Create ruff.toml
    ruff_config_path = project_root / "ruff.toml"
    if not ruff_config_path.exists():
        logger.info(f"Creating {ruff_config_path}...")
        ruff_config = """# Ruff configuration for llmXive project
line-length = 88
target-version = "py311"

[lint]
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
    "C901", # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[lint.isort]
known-first-party = ["lib"]
known-third-party = ["numpy", "pandas", "torch", "onnxruntime", "scipy", "pyproj", "PIL"]
"""
        ruff_config_path.write_text(ruff_config)
    else:
        logger.info(f"{ruff_config_path} already exists, skipping.")

    # Create pyproject.toml for Black if it doesn't exist
    pyproject_path = project_root / "pyproject.toml"
    black_config_exists = False
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            black_config_exists = True
    
    if not black_config_exists:
        logger.info(f"Updating {pyproject_path} with Black configuration...")
        black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.venv
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
"""
        if pyproject_path.exists():
            # Append if exists, otherwise write
            existing = pyproject_path.read_text()
            if not existing.endswith('\n'):
                existing += '\n'
            pyproject_path.write_text(existing + black_config)
        else:
            pyproject_path.write_text(black_config)
    else:
        logger.info(f"Black config already present in {pyproject_path}.")

    logger.info("Linting and formatting configuration created successfully.")

def main():
    """Main entry point for linting setup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting linting configuration setup...")
    
    try:
        install_dev_dependencies()
        create_config_files()
        logger.info("Linting setup completed successfully.")
    except Exception as e:
        logger.error(f"Linting setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()