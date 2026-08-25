import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from utils.logging_utils import get_logger

logger = get_logger(__name__)


def run_command(cmd: List[str], cwd: Path = None) -> Tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Failed to run command {cmd}: {e}")
        return -1, "", str(e)


def check_flake8(root: Path) -> bool:
    """
    Run flake8 on the code directory.
    Returns True if flake8 passes (exit code 0).
    """
    code_dir = root / "code"
    if not code_dir.exists():
        logger.warning(f"Code directory not found: {code_dir}")
        return True

    rc, out, err = run_command(["flake8", str(code_dir)], cwd=root)
    if rc != 0:
        logger.error("flake8 found issues:")
        logger.error(out)
        if err:
            logger.error(err)
        return False
    logger.info("flake8 passed.")
    return True


def check_black(root: Path) -> bool:
    """
    Run black --check on the code directory.
    Returns True if black formatting is correct.
    """
    code_dir = root / "code"
    if not code_dir.exists():
        logger.warning(f"Code directory not found: {code_dir}")
        return True

    rc, out, err = run_command(["black", "--check", str(code_dir)], cwd=root)
    if rc != 0:
        logger.error("black formatting issues found:")
        logger.error(out)
        if err:
            logger.error(err)
        return False
    logger.info("black formatting check passed.")
    return True


def fix_black(root: Path) -> bool:
    """
    Run black to fix formatting issues.
    Returns True if successful.
    """
    code_dir = root / "code"
    if not code_dir.exists():
        logger.warning(f"Code directory not found: {code_dir}")
        return True

    rc, out, err = run_command(["black", str(code_dir)], cwd=root)
    if rc != 0:
        logger.error("black failed to fix formatting:")
        logger.error(err)
        return False
    logger.info("black formatting applied.")
    return True


def setup_config_files(root: Path) -> None:
    """
    Create .flake8 and pyproject.toml configuration files if they don't exist.
    """
    # .flake8 configuration
    flake8_path = root / ".flake8"
    if not flake8_path.exists():
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
"""
        flake8_path.write_text(content)
        logger.info(f"Created {flake8_path}")

    # pyproject.toml for black
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-quantifying-code-ownership"
version = "0.1.0"
description = "Quantifying the impact of code ownership on software quality"
requires-python = ">=3.11"
dependencies = [
    "GitPython",
    "scikit-learn",
    "scipy",
    "pandas",
    "numpy",
    "radon",
    "matplotlib",
    "pyyaml",
    "flake8",
    "black",
    "requests",
]

[tool.black]
line-length = 88
target-version = ['py311']
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
"""
        pyproject_path.write_text(content)
        logger.info(f"Created {pyproject_path}")
    else:
        # Ensure black section exists in existing pyproject.toml
        text = pyproject_path.read_text()
        if "[tool.black]" not in text:
            text += "\n[tool.black]\nline-length = 88\ntarget-version = ['py311']\n"
            pyproject_path.write_text(text)
            logger.info("Updated pyproject.toml with black configuration.")


def main(root: Path = None) -> int:
    """
    Main entry point for linting and formatting configuration.
    If --fix is passed, run black to fix issues.
    If --check is passed (default), run flake8 and black --check.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Lint and format code")
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="Project root directory"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run black to fix formatting issues",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=True,
        help="Run flake8 and black --check (default)",
    )
    args = parser.parse_args()

    root = args.root

    logger.info(f"Project root: {root}")

    # Setup config files
    setup_config_files(root)

    if args.fix:
        logger.info("Running black to fix formatting...")
        if not fix_black(root):
            logger.error("Failed to fix formatting with black.")
            return 1
        logger.info("Formatting fixed. Please run --check to verify.")
        return 0

    if args.check:
        logger.info("Running linting checks...")
        flake8_ok = check_flake8(root)
        black_ok = check_black(root)

        if not flake8_ok or not black_ok:
            logger.error("Linting checks failed.")
            return 1
        logger.info("All linting checks passed.")
        return 0

    return 0