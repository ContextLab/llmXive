"""
Linting and formatting configuration utilities for the DFT-D3 transferability project.

This module provides functions to ensure flake8 and black configuration files
exist in the project root and to run the linting/formatting tools.
"""
import os
import subprocess
import sys
from pathlib import Path

from logger import get_logger, error, info

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FLAKE8_CONFIG = PROJECT_ROOT / ".flake8"
BLACK_CONFIG = PROJECT_ROOT / "pyproject.toml"
ISORT_CONFIG = PROJECT_ROOT / "pyproject.toml"

FLAKE8_CONTENT = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    data/
max-complexity = 10
"""

BLACK_ISORT_CONTENT = """[tool.black]
line-length = 88
target-version = ['py311']
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
  | data
)/
'''

[tool.isort]
profile = "black"
line_length = 88
skip = ["data", ".git", ".tox", ".venv", "build", "dist"]
"""

def ensure_config_files() -> bool:
    """
    Ensure .flake8 and pyproject.toml (for black/isort) exist in the project root.
    Creates them with default settings if they don't exist.

    Returns:
        bool: True if all files exist or were created successfully, False otherwise.
    """
    success = True

    # Ensure .flake8
    if not FLAKE8_CONFIG.exists():
        try:
            with open(FLAKE8_CONFIG, 'w', encoding='utf-8') as f:
                f.write(FLAKE8_CONTENT)
            info(f"Created {FLAKE8_CONFIG}")
        except OSError as e:
            error(f"Failed to create {FLAKE8_CONFIG}: {e}")
            success = False
    else:
        info(f"{FLAKE8_CONFIG} already exists")

    # Ensure pyproject.toml exists for black/isort
    if not BLACK_CONFIG.exists():
        try:
            with open(BLACK_CONFIG, 'w', encoding='utf-8') as f:
                f.write(BLACK_ISORT_CONTENT)
            info(f"Created {BLACK_CONFIG} with black/isort configuration")
        except OSError as e:
            error(f"Failed to create {BLACK_CONFIG}: {e}")
            success = False
    else:
        # Check if sections exist, if not append (simplified: just warn if exists)
        try:
            with open(BLACK_CONFIG, 'r', encoding='utf-8') as f:
                content = f.read()
            if '[tool.black]' not in content:
                logger.warning(f"{BLACK_CONFIG} exists but lacks [tool.black] section. Manual merge may be needed.")
            else:
                info(f"{BLACK_CONFIG} already contains black configuration")
        except OSError as e:
            error(f"Failed to read {BLACK_CONFIG}: {e}")
            success = False

    return success

def run_flake8() -> int:
    """
    Run flake8 on the code/ and tests/ directories.

    Returns:
        int: Exit code from flake8 (0 if successful, non-zero otherwise).
    """
    if not ensure_config_files():
        error("Configuration files missing, cannot run flake8")
        return 1

    cmd = [
        sys.executable, "-m", "flake8",
        str(PROJECT_ROOT / "code"),
        str(PROJECT_ROOT / "tests"),
        "--config", str(FLAKE8_CONFIG)
    ]

    info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        error("flake8 not found. Please install it: pip install flake8")
        return 1
    except Exception as e:
        error(f"Error running flake8: {e}")
        return 1

def run_black(check_only: bool = True) -> int:
    """
    Run black on the code/ and tests/ directories.

    Args:
        check_only: If True, run in check mode (no modifications). If False, format files.

    Returns:
        int: Exit code from black (0 if successful, 1 if changes needed in check mode, non-zero otherwise).
    """
    if not ensure_config_files():
        error("Configuration files missing, cannot run black")
        return 1

    cmd = [
        sys.executable, "-m", "black",
        "--config", str(BLACK_CONFIG)
    ]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")

    cmd.extend([
        str(PROJECT_ROOT / "code"),
        str(PROJECT_ROOT / "tests")
    ])

    info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        error("black not found. Please install it: pip install black")
        return 1
    except Exception as e:
        error(f"Error running black: {e}")
        return 1

def run_isort(check_only: bool = True) -> int:
    """
    Run isort on the code/ and tests/ directories.

    Args:
        check_only: If True, run in check mode. If False, sort imports.

    Returns:
        int: Exit code from isort (0 if successful, 1 if changes needed in check mode).
    """
    if not ensure_config_files():
        error("Configuration files missing, cannot run isort")
        return 1

    cmd = [
        sys.executable, "-m", "isort",
        "--settings-file", str(BLACK_CONFIG)
    ]
    if check_only:
        cmd.append("--check-only")

    cmd.extend([
        str(PROJECT_ROOT / "code"),
        str(PROJECT_ROOT / "tests")
    ])

    info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        error("isort not found. Please install it: pip install isort")
        return 1
    except Exception as e:
        error(f"Error running isort: {e}")
        return 1

def main() -> int:
    """
    Main entry point for the linting configuration and execution.

    Ensures config files exist, then runs flake8, black (check), and isort (check).
    Returns 0 if all checks pass, 1 otherwise.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    info("Starting linting configuration and checks...")

    # Ensure configuration files exist
    if not ensure_config_files():
        error("Failed to ensure configuration files exist.")
        return 1

    # Run checks
    exit_code = 0

    # flake8
    flake8_code = run_flake8()
    if flake8_code != 0:
        error("flake8 found issues.")
        exit_code = 1
    else:
        info("flake8 passed.")

    # black
    black_code = run_black(check_only=True)
    if black_code != 0:
        error("black formatting check failed. Run 'python code/configure_linting.py format' to fix.")
        exit_code = 1
    else:
        info("black formatting check passed.")

    # isort
    isort_code = run_isort(check_only=True)
    if isort_code != 0:
        error("isort import sorting check failed. Run 'python code/configure_linting.py format' to fix.")
        exit_code = 1
    else:
        info("isort import sorting check passed.")

    if exit_code == 0:
        info("All linting and formatting checks passed.")
    else:
        error("Some checks failed. Please fix the issues.")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())