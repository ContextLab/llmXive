"""
Linting and Formatting Configuration and Execution Utilities.

This module provides functions to ensure ruff and black configurations
exist in the project root and to execute linting and formatting checks.
"""
import os
import subprocess
import sys
from pathlib import Path

import tomli
import tomli_w

PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def ensure_ruff_config() -> Path:
    """
    Ensure a valid ruff configuration exists in pyproject.toml.
    If missing or incomplete, adds the [tool.ruff] section with project defaults.
    Returns the path to the config file.
    """
    config = {
        "select": [
            "E", "W",  # pycodestyle
            "F",       # Pyflakes
            "I",       # isort
            "N",       # pep8-naming
            "UP",      # pyupgrade
            "ANN",     # flake8-annotations (optional strictness)
            "S",       # flake8-bandit (security)
            "B",       # flake8-bugbear
            "C4",      # flake8-comprehensions
            "DTZ",     # flake8-datetimez
            "T10",     # flake8-debugger
            "EXE",     # flake8-executable
            "ISC",     # flake8-implicit-str-concat
            "ICN",     # flake8-import-conventions
            "PIE",     # flake8-pie
            "PT",      # flake8-pytest-style
            "Q",       # flake8-quotes
            "RET",     # flake8-return
            "SIM",     # flake8-simplify
            "TCH",     # flake8-type-checking
            "ARG",     # flake8-unused-arguments
            "PTH",     # flake8-use-pathlib
            "ERA",     # eradicate
            "PL",      # Pylint
        ],
        "ignore": [
            "ANN101",  # Missing type annotation for self in method
            "ANN102",  # Missing type annotation for cls in classmethod
            "S101",    # Use of assert detected (often okay in tests/scripts)
            "PLR0913", # Too many arguments to function call
            "PLR2004", # Magic value used in comparison
        ],
        "target-version": "py311",
        "line-length": 88,
        "exclude": [
            ".git",
            "__pycache__",
            "build",
            "dist",
            "venv",
            ".venv",
            "data",
            "results",
            "state",
        ],
    }

    if not PYPROJECT_PATH.exists():
        # Create new file with config
        pyproject_content = {"tool": {"ruff": config}}
        with open(PYPROJECT_PATH, "wb") as f:
            tomli_w.dump(pyproject_content, f)
        return PYPROJECT_PATH

    # Read existing
    with open(PYPROJECT_PATH, "rb") as f:
        try:
            existing_toml = tomli.load(f)
        except tomli.TOMLDecodeError:
            # If malformed, overwrite safely
            existing_toml = {}

    if "tool" not in existing_toml:
        existing_toml["tool"] = {}

    existing_ruff = existing_toml["tool"].get("ruff", {})
    
    # Merge defaults (existing values take precedence, but we ensure structure)
    for key, value in config.items():
        if key not in existing_ruff:
            existing_ruff[key] = value
        elif isinstance(value, list) and isinstance(existing_ruff.get(key), list):
            # Merge lists to ensure we don't lose existing ignores if they were added manually
            # But for select, we want to enforce our standard set. 
            # For simplicity in this task, we overwrite 'select' to ensure compliance,
            # but merge 'ignore' if it exists to keep user customizations.
            if key == "ignore":
                existing_ruff[key] = list(set(existing_ruff[key] + value))
            elif key == "select":
                existing_ruff[key] = value
        elif isinstance(value, dict) and isinstance(existing_ruff.get(key), dict):
            existing_ruff[key].update(value)
        else:
            existing_ruff[key] = value

    existing_toml["tool"]["ruff"] = existing_ruff

    with open(PYPROJECT_PATH, "wb") as f:
        tomli_w.dump(existing_toml, f)

    return PYPROJECT_PATH


def ensure_black_config() -> Path:
    """
    Ensure a valid black configuration exists in pyproject.toml.
    If missing, adds the [tool.black] section.
    Returns the path to the config file.
    """
    config = {
        "line-length": 88,
        "target-version": ["py311"],
        "include": r"\.pyi?$",
        "exclude": r"""
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
              | data
              | results
              | state
            )/
        """,
    }

    if not PYPROJECT_PATH.exists():
        pyproject_content = {"tool": {"black": config}}
        with open(PYPROJECT_PATH, "wb") as f:
            tomli_w.dump(pyproject_content, f)
        return PYPROJECT_PATH

    with open(PYPROJECT_PATH, "rb") as f:
        try:
            existing_toml = tomli.load(f)
        except tomli.TOMLDecodeError:
            existing_toml = {}

    if "tool" not in existing_toml:
        existing_toml["tool"] = {}

    existing_black = existing_toml["tool"].get("black", {})
    existing_black.update(config)
    existing_toml["tool"]["black"] = existing_black

    with open(PYPROJECT_PATH, "wb") as f:
        tomli_w.dump(existing_toml, f)

    return PYPROJECT_PATH


def run_lint() -> int:
    """
    Run ruff check on the codebase.
    Returns 0 on success, non-zero on failure.
    """
    ensure_ruff_config()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True,
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: ruff is not installed. Run 'pip install ruff'.")
        return 1


def run_format() -> int:
    """
    Run black formatter on the codebase.
    Returns 0 on success, non-zero on failure.
    """
    ensure_black_config()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "."],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True,
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: black is not installed. Run 'pip install black'.")
        return 1


def run_isort() -> int:
    """
    Run isort to sort imports.
    Returns 0 on success, non-zero on failure.
    """
    # isort is often run via ruff now, but if standalone is desired:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "."],
            cwd=PROJECT_ROOT,
            capture_output=False,
            text=True,
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: isort is not installed. Run 'pip install isort'.")
        return 1


def main():
    """
    Main entry point for linting and formatting tools.
    Usage: python -m code.lint_config [lint|format|check]
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.lint_config [lint|format|check]")
        print("  lint  : Run ruff check")
        print("  format: Run black formatter")
        print("  check : Run lint check only (no fix)")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "lint":
        print("Running linter (ruff)...")
        exit_code = run_lint()
        if exit_code == 0:
            print("Linter passed.")
        else:
            print("Linter found issues.")
        sys.exit(exit_code)

    elif command == "format":
        print("Running formatter (black)...")
        exit_code = run_format()
        if exit_code == 0:
            print("Formatter completed.")
        else:
            print("Formatter encountered errors.")
        sys.exit(exit_code)

    elif command == "check":
        # Run both, fail if either fails
        print("Running checks (ruff)...")
        lint_code = run_lint()
        if lint_code != 0:
            print("Lint checks failed.")
            sys.exit(lint_code)
        
        print("Running format check (black --check)...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "."],
                cwd=PROJECT_ROOT,
                capture_output=False,
                text=True,
            )
            if result.returncode != 0:
                print("Format checks failed. Run 'python -m code.lint_config format' to fix.")
                sys.exit(result.returncode)
        except FileNotFoundError:
            print("Error: black is not installed.")
            sys.exit(1)

        print("All checks passed.")
        sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
