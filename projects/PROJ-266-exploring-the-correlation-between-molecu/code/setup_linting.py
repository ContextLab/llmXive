"""
Script to configure linting (flake8/black) and formatting tools.
Implements T004: Configure linting (flake8/black) and formatting tools.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Import logger from local utils
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution if utils not in path
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Get the project root directory (parent of 'code')."""
    current = Path(__file__).resolve()
    # Assuming this script is in code/
    return current.parent

def check_config_files(project_root: Path) -> Tuple[bool, List[str]]:
    """Check if flake8 and black config files exist."""
    missing = []
    flake8_cfg = project_root / ".flake8"
    pyproject_cfg = project_root / "pyproject.toml"

    if not flake8_cfg.exists():
        missing.append(".flake8")
    if not pyproject_cfg.exists() or "[tool.black]" not in pyproject_cfg.read_text():
        missing.append("pyproject.toml (black section)")

    return len(missing) == 0, missing

def create_flake8_config(project_root: Path) -> None:
    """Create .flake8 configuration file."""
    content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .eggs,
    *.egg-info,
    build,
    dist
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py: F401
"""
    path = project_root / ".flake8"
    path.write_text(content)
    logger.info(f"Created {path}")

def create_black_config(project_root: Path) -> None:
    """Ensure pyproject.toml has black configuration."""
    pyproject_path = project_root / "pyproject.toml"
    content = pyproject_path.read_text() if pyproject_path.exists() else ""

    if "[tool.black]" not in content:
        black_config = """
[tool.black]
line-length = 88
target-version = ['py38']
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

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v"
"""
        # Append if file exists, otherwise write new
        if pyproject_path.exists():
            with open(pyproject_path, "a") as f:
                f.write(black_config)
        else:
            # Basic build system config if file didn't exist
            header = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "molecular-flexibility-permeability"
version = "0.1.0"
description = "Exploring the correlation between molecular flexibility and drug transport"
requires-python = ">=3.8"
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
    "nolds",
]
"""
            with open(pyproject_path, "w") as f:
                f.write(header + black_config)
        logger.info(f"Updated {pyproject_path} with Black configuration")
    else:
        logger.info(f"{pyproject_path} already contains Black configuration")

def run_flake8_check(project_root: Path) -> int:
    """Run flake8 to check for linting errors."""
    logger.info("Running flake8 check...")
    try:
        result = subprocess.run(
            ["flake8", str(project_root / "code")],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Flake8 check passed.")
            return 0
        else:
            logger.warning("Flake8 found issues:")
            print(result.stdout)
            print(result.stderr)
            return result.returncode
    except FileNotFoundError:
        logger.error("flake8 not found. Please install it: pip install flake8")
        return 1
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return 1

def run_black_check(project_root: Path) -> int:
    """Run black to check for formatting issues."""
    logger.info("Running black check...")
    try:
        result = subprocess.run(
            ["black", "--check", str(project_root / "code")],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("Black check passed.")
            return 0
        else:
            logger.warning("Black found formatting issues. Run 'black code/' to fix.")
            print(result.stdout)
            print(result.stderr)
            return result.returncode
    except FileNotFoundError:
        logger.error("black not found. Please install it: pip install black")
        return 1
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return 1

def main() -> int:
    """Main entry point for setup_linting."""
    logger.info("Starting linting configuration setup (T004)...")
    project_root = get_project_root()

    # 1. Create config files
    logger.info("Checking configuration files...")
    exists, missing = check_config_files(project_root)
    if not exists:
        logger.info(f"Missing configs: {missing}. Creating them now...")
        if ".flake8" in missing:
            create_flake8_config(project_root)
        if "pyproject.toml (black section)" in missing:
            create_black_config(project_root)
    else:
        logger.info("Configuration files already present.")

    # 2. Attempt to run checks (optional, but good for verification)
    # We log warnings but do not fail the setup if tools are missing
    flake8_code = run_flake8_check(project_root)
    black_code = run_black_check(project_root)

    if flake8_code == 0 and black_code == 0:
        logger.info("Linting and formatting setup complete and verified.")
        return 0
    elif flake8_code != 0 or black_code != 0:
        logger.warning("Linting setup complete, but check found issues. "
                       "Run 'black code/' and 'flake8 code/' manually to fix.")
        return 0  # Setup is done, issues are for the developer to fix
    return 0

if __name__ == "__main__":
    sys.exit(main())