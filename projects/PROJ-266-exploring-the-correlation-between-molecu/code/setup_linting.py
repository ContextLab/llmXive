import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple
from utils.logging import get_logger

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "setup_linting.py").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")

def check_config_files(root: Path) -> Tuple[bool, List[str]]:
    """Check if flake8 and black config files exist."""
    missing = []
    if not (root / ".flake8").exists():
        missing.append(".flake8")
    if not (root / "pyproject.toml").exists():
        missing.append("pyproject.toml (for black)")
    return len(missing) == 0, missing

def create_flake8_config(root: Path) -> None:
    """Create .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .eggs,
    build,
    dist,
    *.egg-info,
    .venv,
    venv,
    env,
    data/processed/conformers.pkl
per-file-ignores =
    # Allow long lines in test files for readability
    tests/*: E501
"""
    config_path = root / ".flake8"
    config_path.write_text(config_content)
    logger = get_logger(__name__)
    logger.info(f"Created {config_path}")

def create_black_config(root: Path) -> None:
    """Ensure pyproject.toml exists with black configuration."""
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            # Append black config
            black_config = """

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
  | \\.eggs
)/
'''
"""
            pyproject_path.write_text(content + black_config)
            logger = get_logger(__name__)
            logger.info("Updated pyproject.toml with black configuration")
    else:
        # Create minimal pyproject.toml with black config
        config_content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "molecular-flexibility-permeability"
version = "0.1.0"
description = "Exploring the correlation between molecular flexibility and drug transport across cell membranes"
requires-python = ">=3.9"
dependencies = [
    "rdkit",
    "pandas",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "requests",
    "numpy",
    "scipy",
    "statsmodels",
    "pyvib",
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
  | \\.eggs
)/
'''

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
"""
        pyproject_path.write_text(config_content)
        logger = get_logger(__name__)
        logger.info(f"Created {pyproject_path}")

def run_flake8_check(root: Path) -> bool:
    """Run flake8 check and return True if it passes."""
    logger = get_logger(__name__)
    try:
        result = subprocess.run(
            ["flake8", "code/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("flake8 check passed")
            return True
        else:
            logger.warning("flake8 found issues:")
            logger.warning(result.stdout)
            logger.warning(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it: pip install flake8")
        return False

def run_black_check(root: Path) -> bool:
    """Run black check and return True if it passes."""
    logger = get_logger(__name__)
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("black check passed")
            return True
        else:
            logger.warning("black found formatting issues:")
            logger.warning(result.stdout)
            logger.warning(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return False

def main() -> int:
    """Main entry point for setup_linting script."""
    logger = get_logger(__name__)
    logger.info("Setting up linting and formatting tools...")

    root = get_project_root()
    logger.info(f"Project root: {root}")

    # Check if config files exist
    configs_exist, missing = check_config_files(root)
    if not configs_exist:
        logger.info(f"Missing config files: {missing}")
        logger.info("Creating configuration files...")
        create_flake8_config(root)
        create_black_config(root)
    else:
        logger.info("Configuration files already exist.")

    # Run checks
    flake8_ok = run_flake8_check(root)
    black_ok = run_black_check(root)

    if flake8_ok and black_ok:
        logger.info("All linting and formatting checks passed!")
        return 0
    else:
        logger.warning("Some checks failed. Please fix the issues.")
        if not flake8_ok:
            logger.warning("- Run 'flake8 code/' to see flake8 issues")
        if not black_ok:
            logger.warning("- Run 'black --check code/' to see formatting issues")
            logger.warning("- Run 'black code/' to auto-fix formatting")
        return 1

if __name__ == "__main__":
    sys.exit(main())