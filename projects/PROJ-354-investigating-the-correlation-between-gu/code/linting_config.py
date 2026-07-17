"""
Linting and Formatting Configuration Module.

Provides centralized configuration and execution helpers for:
- Black (code formatter)
- Ruff (linter)

This module ensures consistent code style and quality across the project.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration paths
BLACK_CONFIG_PATH = PROJECT_ROOT / "pyproject.toml"
RUFF_CONFIG_PATH = PROJECT_ROOT / "pyproject.toml"


def get_black_config() -> Dict[str, Any]:
    """
    Returns the default Black configuration for this project.

    Returns:
        Dict containing Black configuration options.
    """
    return {
        "line-length": 88,
        "target-version": ["py310"],
        "skip-string-normalization": False,
        "exclude": r"(\.git|\.hg|\.mypy_cache|\.tox|\.venv|_build|buck-out|build|dist|__pycache__|data/|results/)",
    }


def get_ruff_config() -> Dict[str, Any]:
    """
    Returns the default Ruff configuration for this project.

    Returns:
        Dict containing Ruff configuration options.
    """
    return {
        "line-length": 88,
        "target-version": "py310",
        "select": [
            "E",  # pycodestyle errors
            "W",  # pycodestyle warnings
            "F",  # Pyflakes
            "I",  # isort
            "C",  # flake8-comprehensions
            "B",  # flake8-bugbear
            "UP", # pyupgrade
            "N",  # pep8-naming
        ],
        "ignore": [
            "E501",  # line too long (handled by black)
            "B008",  # do not perform function calls in argument defaults
            "C901",  # too complex
        ],
        "exclude": [
            ".git",
            ".mypy_cache",
            ".tox",
            ".venv",
            "data",
            "results",
            "__pycache__",
        ],
    }


def _write_pyproject_config() -> None:
    """
    Writes the combined Black and Ruff configuration to pyproject.toml.
    This ensures the configuration exists for CLI tools to read.
    """
    config_content = """[tool.black]
line-length = 88
target-version = ['py310']
skip-string-normalization = false
exclude = '''
(
  \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
  | __pycache__
  | data
  | results
)
'''

[tool.ruff]
line-length = 88
target-version = "py310"
select = [
    "E",
    "W",
    "F",
    "I",
    "C",
    "B",
    "UP",
    "N",
]
ignore = [
    "E501",
    "B008",
    "C901",
]
exclude = [
    ".git",
    ".mypy_cache",
    ".tox",
    ".venv",
    "data",
    "results",
    "__pycache__",
]
"""
    config_path = PROJECT_ROOT / "pyproject.toml"
    # Only write if it doesn't exist or to ensure it has the tool sections
    # In a real scenario, we might append or merge, but for this task
    # we ensure the config exists.
    if not config_path.exists():
        config_path.write_text(config_content)
    else:
        # Read existing, check for sections, update if missing (simplified)
        content = config_path.read_text()
        if "[tool.black]" not in content:
            content += "\n" + config_content.split("[tool.black]")[1]
            config_path.write_text(content)


def run_formatter(paths: Optional[List[str]] = None, check_only: bool = False) -> bool:
    """
    Runs Black formatter on the specified paths or the whole project.

    Args:
        paths: List of file/directory paths to format. Defaults to project root.
        check_only: If True, only check formatting without modifying files.

    Returns:
        True if formatting was successful (or check passed), False otherwise.
    """
    _write_pyproject_config()

    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")
    else:
        cmd.append("--quiet")

    if paths:
        cmd.extend(paths)
    else:
        # Default to formatting the 'code' directory and tests
        cmd.append(str(PROJECT_ROOT / "code"))
        cmd.append(str(PROJECT_ROOT / "tests"))

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            if check_only:
                print("Formatting check failed. Please run 'python code/linting_config.py' to format.")
            else:
                print(f"Black formatting error: {result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("Error: 'black' is not installed. Please install it via requirements.txt.")
        return False
    except Exception as e:
        print(f"Error running Black: {e}")
        return False


def run_linter(paths: Optional[List[str]] = None, fix: bool = False) -> bool:
    """
    Runs Ruff linter on the specified paths or the whole project.

    Args:
        paths: List of file/directory paths to lint. Defaults to project root.
        fix: If True, attempt to automatically fix issues.

    Returns:
        True if linting passed (or fixes applied successfully), False otherwise.
    """
    _write_pyproject_config()

    cmd = [sys.executable, "-m", "ruff"]
    if fix:
        cmd.append("--fix")
        cmd.append("--exit-zero") # Exit 0 even if fixes were applied
    else:
        cmd.append("--output-format=full")

    if paths:
        cmd.extend(paths)
    else:
        cmd.append(str(PROJECT_ROOT / "code"))
        cmd.append(str(PROJECT_ROOT / "tests"))

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            if not fix:
                print("Linting failed. Run with fix=True to attempt automatic fixes.")
            return False
        return True
    except FileNotFoundError:
        print("Error: 'ruff' is not installed. Please install it via requirements.txt.")
        return False
    except Exception as e:
        print(f"Error running Ruff: {e}")
        return False


def validate_environment() -> bool:
    """
    Checks if the required linting and formatting tools are installed.

    Returns:
        True if all tools are available, False otherwise.
    """
    tools = ["black", "ruff"]
    missing = []

    for tool in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", tool, "--version"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)

    if missing:
        print(f"Missing required tools: {', '.join(missing)}. "
              f"Please install them: pip install {' '.join(missing)}")
        return False

    print("All linting and formatting tools are installed.")
    return True


def main():
    """
    Command-line entry point for linting and formatting tasks.

    Usage:
      python code/linting_config.py check      # Check formatting and linting
      python code/linting_config.py format     # Format code
      python code/linting_config.py lint       # Lint code
      python code/linting_config.py fix        # Fix linting issues
      python code/linting_config.py validate   # Check tool installation
    """
    import argparse

    parser = argparse.ArgumentParser(description="Linting and Formatting utilities")
    parser.add_argument(
        "action",
        choices=["check", "format", "lint", "fix", "validate"],
        help="Action to perform",
    )
    args = parser.parse_args()

    success = True

    if args.action == "validate":
        success = validate_environment()
    elif args.action == "check":
        print("Checking formatting...")
        success = run_formatter(check_only=True) and success
        print("Checking linting...")
        success = run_linter() and success
    elif args.action == "format":
        print("Formatting code...")
        success = run_formatter() and success
    elif args.action == "lint":
        print("Linting code...")
        success = run_linter() and success
    elif args.action == "fix":
        print("Fixing linting issues...")
        success = run_linter(fix=True) and success

    if success:
        print("All checks passed.")
        sys.exit(0)
    else:
        print("Some checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()