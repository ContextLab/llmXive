"""
setup_linting.py
-----------------
Script to configure project-wide linting (ruff, flake8) and formatting (black)
tools. When executed, it creates the necessary configuration files at the
repository root:
  - pyproject.toml   (black configuration)
  - .ruff.toml       (ruff configuration)
  - .flake8          (flake8 configuration)
The script is idempotent: existing files will be overwritten with the
canonical configuration required by the project.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def write_file(file_path: Path, content: str) -> None:
    """Write *content* to *file_path*, creating parent directories if needed."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    log.info("Wrote configuration file: %s", file_path)


def create_black_config(root: Path) -> None:
    """Create a pyproject.toml with Black formatting settings."""
    black_toml = """[tool.black]
line-length = 88
target-version = ['py310']
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
    write_file(root / "pyproject.toml", black_toml)


def create_ruff_config(root: Path) -> None:
    """Create a .ruff.toml with sensible defaults."""
    ruff_toml = """[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
exclude = ["__pycache__", ".git", "build", "dist"]
"""
    write_file(root / ".ruff.toml", ruff_toml)


def create_flake8_config(root: Path) -> None:
    """Create a .flake8 configuration file."""
    flake8_cfg = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
"""
    write_file(root / ".flake8", flake8_cfg)


def main() -> None:
    """
    Entry point for the linting/formatting configuration script.

    It writes the three configuration files to the project root
    (the directory returned by ``paths.root``).  The function exits
    with a non‑zero status code if any unexpected error occurs.
    """
    try:
        project_root = Path(paths.root)
        log.info("Configuring linting/formatting tools in %s", project_root)

        create_black_config(project_root)
        create_ruff_config(project_root)
        create_flake8_config(project_root)

        log.info("Linting and formatting configuration completed successfully.")
    except Exception as exc:  # pragma: no cover – unexpected failures are fatal
        log.error("Failed to configure linting/formatting tools: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
