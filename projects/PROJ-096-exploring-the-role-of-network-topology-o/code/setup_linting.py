import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and log the result.
    
    Args:
        cmd: Command and arguments as a list of strings.
        description: Human-readable description of the action.
        
    Returns:
        True if the command succeeded, False otherwise.
    """
    logger.info(f"Executing: {description}")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.debug(f"Output:\n{result.stdout}")
        logger.info(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute: {description}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        logger.error("Please ensure the tool is installed (e.g., pip install flake8 black).")
        return False

def main():
    """
    Main entry point to configure linting (flake8) and formatting (black).
    
    This function:
    1. Installs flake8 and black if not present.
    2. Creates a .flake8 configuration file.
    3. Creates a pyproject.toml file with Black configuration.
    4. Optionally installs pre-commit hooks if pre-commit is available.
    """
    project_root = Path(__file__).resolve().parent.parent
    logger.info(f"Project root detected at: {project_root}")

    # 1. Ensure tools are installed
    tools = [
        (["pip", "install", "-q", "flake8", "black"], "Installing flake8 and black"),
    ]
    
    for cmd, desc in tools:
        if not run_command(cmd, desc):
            logger.warning(f"Could not install tool via pip. Please install manually: {' '.join(cmd)}")

    # 2. Create .flake8 configuration
    flake8_config_path = project_root / ".flake8"
    flake8_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
"""
    logger.info(f"Writing flake8 configuration to: {flake8_config_path}")
    with open(flake8_config_path, 'w') as f:
        f.write(flake8_content)
    
    # 3. Create pyproject.toml with Black configuration
    pyproject_path = project_root / "pyproject.toml"
    
    # Check if pyproject.toml already exists to avoid overwriting user config
    black_config_exists = False
    if pyproject_path.exists():
        with open(pyproject_path, 'r') as f:
            content = f.read()
            if '[tool.black]' in content:
                black_config_exists = True
                logger.info("Black configuration already exists in pyproject.toml, skipping creation.")
    
    if not black_config_exists:
        black_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
        logger.info(f"Writing Black configuration to: {pyproject_path}")
        with open(pyproject_path, 'w') as f:
            f.write(black_content)

    # 4. Optional: Pre-commit setup
    logger.info("Attempting to set up pre-commit hooks...")
    if run_command(["pip", "install", "-q", "pre-commit"], "Installing pre-commit"):
        pre_commit_config_path = project_root / ".pre-commit-config.yaml"
        pre_commit_content = """repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
- id: black
  language_version: python3.11
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8
"""
        logger.info(f"Writing pre-commit configuration to: {pre_commit_config_path}")
        with open(pre_commit_config_path, 'w') as f:
            f.write(pre_commit_content)
        
        run_command(["pre-commit", "install"], "Installing pre-commit git hook")
    else:
        logger.warning("Pre-commit not installed. Skipping hook setup.")

    logger.info("Linting and formatting configuration complete.")
    logger.info("To run linting: flake8 code/")
    logger.info("To run formatting: black code/")

if __name__ == "__main__":
    main()