"""
Script to ensure linting (ruff/flake8) and formatting (black) configuration files
are present in the project root. If any of the expected config files are missing,
they are created with sensible defaults.

This script is idempotent – running it multiple times will not overwrite existing
files unless they are empty.
"""
import os
import sys
from pathlib import Path
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def check_file_exists(path: str, description: str) -> bool:
    """
    Verify that a file exists and is non‑empty.

    Args:
        path: Relative path (from project root) to the file.
        description: Human‑readable description used in log messages.

    Returns:
        True if the file exists and has size > 0, False otherwise.
    """
    file_path = Path(path)
    if file_path.is_file() and file_path.stat().st_size > 0:
        log.info(f"{description} already exists at {file_path}")
        return True
    log.warning(f"{description} not found or empty at {file_path}")
    return False

# ----------------------------------------------------------------------
# Configuration file templates
# ----------------------------------------------------------------------
RUFF_TOML_CONTENT = """\
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
fix = true
"""

FLAKE8_CONTENT = """\
[flake8]
max-line-length = 88
extend-ignore = E203
"""

PYPROJECT_TOML_CONTENT = """\
[tool.black]
line-length = 88
target-version = ["py311"]
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
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

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Ensure all linting/formatting configuration files exist.
    Creates missing files with default content.
    """
    project_root = Path(__file__).resolve().parents[2]  # <project>/code/scripts/../..
    os.chdir(project_root)  # Ensure relative paths resolve from project root

    # Define the files we want to guarantee
    files = [
        (".ruff.toml", RUFF_TOML_CONTENT, "Ruff configuration"),
        (".flake8", FLAKE8_CONTENT, "Flake8 configuration"),
        ("pyproject.toml", PYPROJECT_TOML_CONTENT, "Black configuration (pyproject)"),
    ]

    for rel_path, content, description in files:
        target_path = project_root / rel_path
        if not check_file_exists(str(target_path), description):
            try:
                target_path.write_text(content, encoding="utf-8")
                log.info(f"Created {description} at {target_path}")
            except Exception as exc:
                log.error(f"Failed to write {description} to {target_path}: {exc}")
                sys.exit(1)

    log.info("Linting and formatting configuration files are now set up.")

if __name__ == "__main__":
    main()
