"""
Linting and Formatting Configuration for llmXive Project.

This module provides setup and verification for Ruff (linting) and Black (formatting).
It ensures that the project adheres to the defined code style standards.
"""
import os
import sys
import subprocess
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "results"

# Configuration file paths
RUFF_CONFIG = PROJECT_ROOT / "pyproject.toml"
BLACK_CONFIG = PROJECT_ROOT / "pyproject.toml"

def ensure_ruff_black_installed():
    """
    Check if ruff and black are installed. If not, attempt to install them.
    Raises an error if installation fails or tools are unavailable.
    """
    tools = [
        ("ruff", "ruff --version"),
        ("black", "black --version")
    ]
    
    missing = []
    for tool_name, check_cmd in tools:
        try:
            subprocess.run(
                check_cmd.split(),
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"{tool_name} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool_name)
    
    if missing:
        logger.warning(f"Missing tools: {', '.join(missing)}. Attempting to install...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "ruff", "black"],
                check=True,
                cwd=PROJECT_ROOT
            )
            logger.info("Successfully installed missing tools.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install linting tools: {e}")

def create_pyproject_config():
    """
    Create or update pyproject.toml with Ruff and Black configuration.
    """
    config_content = """
[tool.black]
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
)/
'''

[tool.ruff]
# Same as Black.
line-length = 88
target-version = "py311"

# Assume Python 3.11
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

# Exclude a few directories
exclude = [
    ".git",
    ".tox",
    ".venv",
    "build",
    "dist",
    "data",
    "results",
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"] # Ignore unused imports in init files
"""
    
    if not RUFF_CONFIG.exists():
        with open(RUFF_CONFIG, "w") as f:
            f.write(config_content)
        logger.info(f"Created {RUFF_CONFIG} with linting configuration.")
    else:
        logger.info(f"{RUFF_CONFIG} already exists. Skipping creation.")

def check_config_files():
    """
    Verify that linting configuration files exist and are valid.
    """
    ensure_ruff_black_installed()
    create_pyproject_config()
    
    logger.info("Linting configuration check complete.")
    return True

def run_lint_check():
    """
    Run ruff to check for linting errors.
    """
    ensure_ruff_black_installed()
    try:
        result = subprocess.run(
            ["ruff", "check", str(CODE_DIR), str(TESTS_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.warning("Ruff found issues:")
            print(result.stdout)
            print(result.stderr)
            return False
        else:
            logger.info("Ruff check passed.")
            return True
    except Exception as e:
        logger.error(f"Error running ruff: {e}")
        return False

def run_format_check():
    """
    Run black to check for formatting issues (dry run).
    """
    ensure_ruff_black_installed()
    try:
        result = subprocess.run(
            ["black", "--check", str(CODE_DIR), str(TESTS_DIR)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.warning("Black found formatting issues:")
            print(result.stdout)
            print(result.stderr)
            return False
        else:
            logger.info("Black check passed.")
            return True
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False

def main():
    """
    Main entry point for linting setup and verification.
    """
    parser = argparse.ArgumentParser(description="Setup and verify linting tools.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run linting and formatting checks without fixing."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run linting fixes (ruff) and formatting fixes (black)."
    )
    
    args = parser.parse_args()
    
    # Ensure configuration exists
    create_pyproject_config()
    
    if args.check:
        lint_ok = run_lint_check()
        format_ok = run_format_check()
        if lint_ok and format_ok:
            logger.info("All checks passed.")
            sys.exit(0)
        else:
            logger.error("Some checks failed.")
            sys.exit(1)
    elif args.fix:
        ensure_ruff_black_installed()
        logger.info("Running ruff fix...")
        subprocess.run(["ruff", "check", "--fix", str(CODE_DIR), str(TESTS_DIR)], cwd=PROJECT_ROOT)
        logger.info("Running black format...")
        subprocess.run(["black", str(CODE_DIR), str(TESTS_DIR)], cwd=PROJECT_ROOT)
        logger.info("Fixes applied.")
    else:
        logger.info("Linting tools configured successfully.")
        logger.info("Run `python code/linting_setup.py --check` to verify.")
        logger.info("Run `python code/linting_setup.py --fix` to apply fixes.")

if __name__ == "__main__":
    main()