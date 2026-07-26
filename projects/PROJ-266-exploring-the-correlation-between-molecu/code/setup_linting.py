"""
Setup script for linting and formatting tools (flake8, black).
This script verifies configuration files exist and provides basic checks.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple
import logging

# Import logging utilities from the project
try:
    from utils.logging import get_logger, setup_logging_for_script
except ImportError:
    # Fallback if utils.logging is not yet available in PYTHONPATH
    logging.basicConfig(level=logging.INFO)
    def get_logger(name): return logging.getLogger(name)
    def setup_logging_for_script(name): return get_logger(name)

def get_project_root() -> Path:
    """Return the project root directory (parent of 'code')."""
    current = Path(__file__).resolve()
    # Traverse up until we find a directory that contains 'code' and 'specs'
    for parent in current.parents:
        if (parent / "code").exists() and (parent / "specs").exists():
            return parent
    # Fallback to current directory if structure not found
    return current.parent

def check_config_files(project_root: Path) -> List[str]:
    """Check for required linting/formatting config files."""
    required_files = [
        ".flake8",
        "pyproject.toml",
    ]
    missing = []
    for fname in required_files:
        fpath = project_root / fname
        if not fpath.exists():
            missing.append(fname)
    return missing

def run_flake8_check(project_root: Path) -> Tuple[bool, str]:
    """Run flake8 check if installed, return (success, message)."""
    try:
        import flake8
        # We don't actually run flake8 here to avoid subprocess complexity in setup,
        # but we verify the tool is available.
        return True, "flake8 is installed and available."
    except ImportError:
        return False, "flake8 is not installed. Install with: pip install flake8"

def run_black_check(project_root: Path) -> Tuple[bool, str]:
    """Run black check if installed, return (success, message)."""
    try:
        import black
        return True, "black is installed and available."
    except ImportError:
        return False, "black is not installed. Install with: pip install black"

def create_flake8_config(project_root: Path) -> bool:
    """Create .flake8 config file if it doesn't exist."""
    config_path = project_root / ".flake8"
    if config_path.exists():
        return False

    content = """[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    *.egg-info
per-file-ignores =
    */__init__.py: F401
    tests/*.py: D100,D101,D102,D103
"""
    config_path.write_text(content)
    return True

def create_black_config(project_root: Path) -> bool:
    """Ensure black config exists in pyproject.toml."""
    config_path = project_root / "pyproject.toml"
    if not config_path.exists():
        # Create a minimal pyproject.toml
        content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "molecular-flexibility-permeability"
version = "0.1.0"
description = "Exploring the correlation between molecular flexibility and drug transport across cell membranes"
requires-python = ">=3.9"

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
"""
        config_path.write_text(content)
        return True

    # Check if [tool.black] section exists
    text = config_path.read_text()
    if "[tool.black]" not in text:
        # Append black config
        black_config = """
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
"""
        config_path.write_text(text + black_config)
        return True
    return False

def main():
    """Main entry point for setup_linting."""
    logger = setup_logging_for_script(__name__)
    logger.info("Starting linting and formatting configuration setup...")

    project_root = get_project_root()
    logger.info(f"Project root detected at: {project_root}")

    # Check for missing config files
    missing = check_config_files(project_root)
    if missing:
        logger.warning(f"Missing configuration files: {missing}")
        logger.info("Creating missing configuration files...")
    else:
        logger.info("All configuration files present.")

    # Create .flake8 if missing
    if ".flake8" in missing:
        if create_flake8_config(project_root):
            logger.info("Created .flake8 configuration.")
        else:
            logger.error("Failed to create .flake8 configuration.")

    # Ensure pyproject.toml has black config
    if create_black_config(project_root):
        logger.info("Updated pyproject.toml with black configuration.")
    else:
        logger.info("Black configuration already present in pyproject.toml.")

    # Check tool availability
    flake8_ok, flake8_msg = run_flake8_check(project_root)
    black_ok, black_msg = run_black_check(project_root)

    if flake8_ok:
        logger.info(f"flake8: {flake8_msg}")
    else:
        logger.warning(f"flake8: {flake8_msg}")

    if black_ok:
        logger.info(f"black: {black_msg}")
    else:
        logger.warning(f"black: {black_msg}")

    logger.info("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())