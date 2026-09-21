"""
Linting and formatting configuration and execution utilities.

This module provides functions to ensure configuration files exist
and to run flake8, black, and isort on the project codebase.
"""
import os
import subprocess
import sys
from pathlib import Path
from logger import get_logger, error, info

logger = get_logger(__name__)


def ensure_config_files():
    """
    Ensure .flake8 and pyproject.toml (for black/isort) exist in the project root.
    Creates them with standard configurations if they do not exist.
    """
    root = Path(__file__).parent.parent
    flake8_config = root / ".flake8"
    pyproject_config = root / "pyproject.toml"

    if not flake8_config.exists():
        logger.info(f"Creating .flake8 configuration at {flake8_config}")
        config_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
extend-ignore = E203, E501
"""
        flake8_config.write_text(config_content)
    else:
        logger.debug(f".flake8 already exists at {flake8_config}")

    if not pyproject_config.exists():
        logger.info(f"Creating pyproject.toml configuration at {pyproject_config}")
        config_content = """[tool.black]
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
"""
        pyproject_config.write_text(config_content)
    else:
        logger.debug(f"pyproject.toml already exists at {pyproject_config}")

    return True


def run_flake8():
    """
    Run flake8 on the code/ and tests/ directories.
    Returns a tuple (success: bool, output: str).
    """
    root = Path(__file__).parent.parent
    flake8_path = root / "code"
    tests_path = root / "tests"

    if not flake8_path.exists() or not tests_path.exists():
        error("Code or tests directory not found.")
        return False, "Directory not found"

    try:
        result = subprocess.run(
            ["flake8", str(flake8_path), str(tests_path)],
            cwd=root,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        if result.returncode != 0:
            error("Flake8 found issues:")
            error(output)
            return False, output
        else:
            info("Flake8 passed: No issues found.")
            return True, output
    except FileNotFoundError:
        error("flake8 not found. Please install it: pip install flake8")
        return False, "flake8 not found"
    except Exception as e:
        error(f"Error running flake8: {e}")
        return False, str(e)


def run_black():
    """
    Run black on the code/ and tests/ directories.
    Returns a tuple (success: bool, output: str).
    """
    root = Path(__file__).parent.parent
    flake8_path = root / "code"
    tests_path = root / "tests"

    if not flake8_path.exists() or not tests_path.exists():
        error("Code or tests directory not found.")
        return False, "Directory not found"

    try:
        result = subprocess.run(
            ["black", "--check", str(flake8_path), str(tests_path)],
            cwd=root,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        if result.returncode != 0:
            error("Black formatting check failed. Run 'black code/ tests/' to fix.")
            error(output)
            return False, output
        else:
            info("Black formatting check passed.")
            return True, output
    except FileNotFoundError:
        error("black not found. Please install it: pip install black")
        return False, "black not found"
    except Exception as e:
        error(f"Error running black: {e}")
        return False, str(e)


def run_isort():
    """
    Run isort on the code/ and tests/ directories.
    Returns a tuple (success: bool, output: str).
    """
    root = Path(__file__).parent.parent
    flake8_path = root / "code"
    tests_path = root / "tests"

    if not flake8_path.exists() or not tests_path.exists():
        error("Code or tests directory not found.")
        return False, "Directory not found"

    try:
        result = subprocess.run(
            ["isort", "--check-only", str(flake8_path), str(tests_path)],
            cwd=root,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        if result.returncode != 0:
            error("isort import sorting check failed. Run 'isort code/ tests/' to fix.")
            error(output)
            return False, output
        else:
            info("isort import sorting check passed.")
            return True, output
    except FileNotFoundError:
        error("isort not found. Please install it: pip install isort")
        return False, "isort not found"
    except Exception as e:
        error(f"Error running isort: {e}")
        return False, str(e)


def main():
    """
    Main entry point to run all linting and formatting checks.
    Ensures config files exist, then runs flake8, black, and isort.
    """
    logger.info("Starting linting and formatting checks...")

    ensure_config_files()

    all_passed = True

    # Run flake8
    success, output = run_flake8()
    if not success:
        all_passed = False

    # Run black
    success, output = run_black()
    if not success:
        all_passed = False

    # Run isort
    success, output = run_isort()
    if not success:
        all_passed = False

    if all_passed:
        logger.info("All linting and formatting checks passed.")
        return 0
    else:
        logger.error("Some checks failed. Please fix the issues and re-run.")
        return 1


if __name__ == "__main__":
    sys.exit(main())