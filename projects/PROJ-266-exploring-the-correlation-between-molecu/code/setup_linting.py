"""
Script to configure linting (flake8) and formatting (black) tools.
This script ensures configuration files exist and runs an initial check.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Add project root to path to import utils
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent


def check_config_files() -> Tuple[bool, List[str]]:
    """Check if flake8 and black config files exist."""
    missing = []
    root = get_project_root()
    flake8_path = root / ".flake8"
    black_path = root / "pyproject.toml"

    if not flake8_path.exists():
        missing.append(".flake8")
    if not black_path.exists() or "tool.black" not in black_path.read_text():
        missing.append("pyproject.toml (black section)")

    return len(missing) == 0, missing


def create_flake8_config() -> None:
    """Create .flake8 configuration file."""
    root = get_project_root()
    config_path = root / ".flake8"
    content = """[flake8]
max-line-length = 100
ignore = E203, E266, W503
per-file-ignores =
    */__init__.py: F401
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
"""
    config_path.write_text(content)
    logger.info(f"Created {config_path}")


def create_black_config() -> None:
    """Ensure pyproject.toml has black configuration."""
    root = get_project_root()
    config_path = root / "pyproject.toml"
    black_section = """
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']
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
)/
'''
"""
    
    if not config_path.exists():
        config_path.write_text(f"[build-system]\nrequires = [\"setuptools>=45\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"{black_section}")
    else:
        current_content = config_path.read_text()
        if "[tool.black]" not in current_content:
            config_path.write_text(current_content + black_section)
    
    logger.info(f"Ensured {config_path} contains black configuration")


def run_flake8_check() -> int:
    """Run flake8 check and return exit code."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["flake8", "code/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Flake8 check passed.")
        else:
            logger.warning("Flake8 found issues:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it: pip install flake8")
        return 1


def run_black_check() -> int:
    """Run black check (diff mode) and return exit code."""
    root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Black check passed.")
        else:
            logger.warning("Black formatting issues found. Run 'black code/' to fix.")
            # Do not print full diff to avoid cluttering logs
        return result.returncode
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return 1


def main() -> None:
    """Main entry point for linting setup."""
    logger.info("Starting linting and formatting configuration...")
    
    # Ensure configs exist
    exists, missing = check_config_files()
    if not exists:
        logger.info(f"Missing configuration files: {missing}")
        if ".flake8" in missing:
            create_flake8_config()
        if "pyproject.toml (black section)" in missing:
            create_black_config()
    
    # Run checks
    flake8_code = run_flake8_check()
    black_code = run_black_check()
    
    if flake8_code == 0 and black_code == 0:
        logger.info("Linting and formatting configuration complete and clean.")
        sys.exit(0)
    else:
        logger.warning("Linting or formatting issues detected. Please fix them.")
        sys.exit(1)


if __name__ == "__main__":
    main()