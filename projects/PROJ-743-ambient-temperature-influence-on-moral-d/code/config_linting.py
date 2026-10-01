"""
Configuration and verification utilities for linting and formatting.
This module ensures that pyproject.toml and ruff.toml are correctly configured
and that the codebase passes `ruff check` and `black --check`.
"""
import os
import sys
import tomli
import tomli_w
from pathlib import Path
from config import get_path_env_override
import subprocess
import logging

def ensure_pyproject_toml(root: Path) -> None:
    """Ensure pyproject.toml exists with Black and Ruff sections."""
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        logging.error(f"pyproject.toml not found at {pyproject_path}")
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)

    # Ensure [tool.black] exists
    if "tool" not in config or "black" not in config.get("tool", {}):
        logging.warning("Missing [tool.black] section in pyproject.toml. Adding defaults.")
        if "tool" not in config:
            config["tool"] = {}
        config["tool"]["black"] = {
            "line-length": 88,
            "target-version": ["py39", "py310", "py311"],
            "include": r"\.pyi?$",
            "exclude": r"/(\.git|\.hg|\.mypy_cache|\.tox|\.venv|_build|buck-out|build|dist)/"
        }

    # Ensure [tool.ruff] exists
    if "tool" not in config or "ruff" not in config.get("tool", {}):
        logging.warning("Missing [tool.ruff] section in pyproject.toml. Adding defaults.")
        if "tool" not in config:
            config["tool"] = {}
        config["tool"]["ruff"] = {
            "line-length": 88,
            "target-version": "py39",
            "select": ["E", "W", "F", "I", "C", "B"],
            "ignore": ["E501", "B008", "C901"]
        }

    # Write back if changed (optional, but ensures consistency)
    with open(pyproject_path, "wb") as f:
        tomli_w.dump(config, f)

def ensure_ruff_config(root: Path) -> None:
    """Ensure ruff.toml exists."""
    ruff_path = root / "ruff.toml"
    if not ruff_path.exists():
        logging.info(f"Creating ruff.toml at {ruff_path}")
        content = """
# Ruff configuration
line-length = 88
target-version = "py39"

[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "C",   # flake8-comprehensions
    "B",   # flake8-bugbear
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"""
        with open(ruff_path, "w") as f:
            f.write(content.strip())

def ensure_flake8_config(root: Path) -> None:
    """Optional: Ensure .flake8 or setup.cfg exists if needed, but we prioritize Ruff."""
    # For this project, we rely on Ruff, so this is a no-op or placeholder.
    pass

def run_linting_checks(root: Path) -> bool:
    """Run ruff check and black --check."""
    logging.info("Running Ruff check...")
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logging.error("Ruff check failed:\n%s", result.stdout)
            logging.error("Errors:\n%s", result.stderr)
            return False
        logging.info("Ruff check passed.")
    except FileNotFoundError:
        logging.error("Ruff not found in PATH. Please install it.")
        return False

    logging.info("Running Black check...")
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=root,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logging.error("Black check failed:\n%s", result.stdout)
            logging.error("Errors:\n%s", result.stderr)
            return False
        logging.info("Black check passed.")
    except FileNotFoundError:
        logging.error("Black not found in PATH. Please install it.")
        return False

    return True

def main():
    """Main entry point for T009."""
    root = Path(get_path_env_override("PROJECT_ROOT", "."))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    logging.info(f"Configuring linting for project at {root}")
    ensure_pyproject_toml(root)
    ensure_ruff_config(root)

    if run_linting_checks(root):
        logging.info("All linting and formatting checks passed.")
        sys.exit(0)
    else:
        logging.error("Linting or formatting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()