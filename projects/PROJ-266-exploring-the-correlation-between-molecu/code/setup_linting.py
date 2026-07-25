"""
Script to configure linting (flake8/black) and formatting tools.

This script:
1. Creates .flake8 configuration file
2. Creates pyproject.toml with black configuration
3. Verifies configuration files are valid
4. Optionally runs initial checks to ensure tools are available
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple
import logging
from utils.logging import get_logger, setup_logging_for_script
from utils.config import get_project_root

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return get_project_root()

def check_config_files(root: Path) -> Tuple[bool, List[str]]:
    """
    Check if linting configuration files exist.
    
    Returns:
        Tuple of (all_exist, missing_files)
    """
    required_files = [
        root / ".flake8",
        root / "pyproject.toml"
    ]
    
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f))
    
    return len(missing) == 0, missing

def run_flake8_check(root: Path) -> bool:
    """
    Run flake8 to check if it's available and working.
    
    Returns:
        True if flake8 is available and passes basic check, False otherwise.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["flake8", "--version"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"flake8 available: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"flake8 check failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it: pip install flake8")
        return False
    except subprocess.TimeoutExpired:
        logger.error("flake8 check timed out")
        return False

def run_black_check(root: Path) -> bool:
    """
    Run black to check if it's available and working.
    
    Returns:
        True if black is available and passes basic check, False otherwise.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["black", "--version"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"black available: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"black check failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return False
    except subprocess.TimeoutExpired:
        logger.error("black check timed out")
        return False

def create_flake8_config(root: Path) -> None:
    """Create .flake8 configuration file."""
    config_content = """[flake8]
# Maximum line length
max-line-length = 88

# Ignore specific errors
# E501: line too long (handled by black)
# W503: line break before binary operator (incompatible with black)
# E203: whitespace before ':' (incompatible with black)
ignore = E501, W503, E203

# Exclude directories
exclude = 
    .git,
    __pycache__,
    .eggs,
    *.egg-info,
    build,
    dist,
    .tox,
    .venv,
    venv

# Max complexity for cyclomatic complexity check
max-complexity = 10

# Show source code snippets
show-source = True

# Show violations
statistics = True
"""
    flake8_path = root / ".flake8"
    with open(flake8_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    logger.info(f"Created {flake8_path}")

def create_black_config(root: Path) -> None:
    """Create pyproject.toml with black configuration."""
    # Check if pyproject.toml already exists
    pyproject_path = root / "pyproject.toml"
    
    if pyproject_path.exists():
        # Read existing content
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if [tool.black] section already exists
        if "[tool.black]" in content:
            logger.info("pyproject.toml already contains [tool.black] section")
            return
        
        # Append black configuration
        black_config = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.eggs
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
            f.write(black_config)
        logger.info(f"Appended [tool.black] section to {pyproject_path}")
    else:
        # Create new pyproject.toml with black configuration
        pyproject_content = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.eggs
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.flake8]
max-line-length = 88
ignore = E501, W503, E203
exclude = .git,__pycache__,.eggs,*.egg-info,build,dist,.tox,.venv,venv
max-complexity = 10
show-source = True
statistics = True
"""
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(pyproject_content)
        logger.info(f"Created {pyproject_path} with black configuration")

def main() -> int:
    """
    Main function to configure linting and formatting tools.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    setup_logging_for_script(__name__)
    
    root = get_project_root()
    logger.info(f"Configuring linting tools for project at: {root}")
    
    # Create configuration files
    try:
        create_flake8_config(root)
        create_black_config(root)
    except Exception as e:
        logger.error(f"Failed to create configuration files: {e}")
        return 1
    
    # Verify configuration files exist
    all_exist, missing = check_config_files(root)
    if not all_exist:
        logger.error(f"Missing configuration files: {missing}")
        return 1
    
    logger.info("Configuration files created successfully")
    
    # Check if tools are available
    flake8_ok = run_flake8_check(root)
    black_ok = run_black_check(root)
    
    if not flake8_ok or not black_ok:
        logger.warning(
            "Some linting tools are not available. "
            "Please install them using: pip install flake8 black"
        )
        # Don't fail if tools are missing, just warn
        # The configuration files are still valid
    
    logger.info("Linting and formatting configuration complete")
    logger.info("To run linter: flake8 code/")
    logger.info("To run formatter: black code/")
    logger.info("To check formatting: black --check code/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())