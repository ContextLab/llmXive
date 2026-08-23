"""
Script to initialize linting and formatting configuration for the project.
This script ensures that .ruff.toml, .black.toml, and .pre-commit-config.yaml
exist in the code directory and are properly configured.
"""

import os
import sys
import shutil
from pathlib import Path

# Define configuration file contents
RUFF_CONFIG = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401", "F403"]  # Allow unused imports and star imports in init files

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""

BLACK_CONFIG = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
"""

PRE_COMMIT_CONFIG = """repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        language_version: python3
        args: [--config=code/.black.toml]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
      - id: ruff
        args: [--config=code/.ruff.toml, --fix]
      - id: ruff-format
        args: [--config=code/.ruff.toml]
"""

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists."""
    if not path.exists():
        path.mkdir(parents=True)
        print(f"Created directory: {path}")

def write_config_file(config_path: Path, content: str) -> None:
    """Write configuration content to a file."""
    if config_path.exists():
        print(f"Configuration file already exists: {config_path}")
        response = input("Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping file overwrite.")
            return

    config_path.write_text(content)
    print(f"Written configuration: {config_path}")

def main() -> int:
    """Main entry point for the setup script."""
    # Determine project root (parent of 'code' directory)
    current_dir = Path(__file__).resolve().parent
    code_dir = current_dir.parent

    # Define configuration file paths
    ruff_path = code_dir / ".ruff.toml"
    black_path = code_dir / ".black.toml"
    pre_commit_path = code_dir / ".pre-commit-config.yaml"

    print("Setting up linting and formatting tools...")

    # Write configuration files
    write_config_file(ruff_path, RUFF_CONFIG)
    write_config_file(black_path, BLACK_CONFIG)
    write_config_file(pre_commit_path, PRE_COMMIT_CONFIG)

    # Create .gitignore entry if not present
    gitignore_path = code_dir / ".gitignore"
    gitignore_entries = [
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        ".ruff_cache/",
        ".mypy_cache/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".tox/",
        "venv/",
        ".venv/",
        "env/",
        ".env/",
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        for entry in gitignore_entries:
            if entry not in content:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{entry}\n")
                print(f"Added '{entry}' to .gitignore")
    else:
        gitignore_path.write_text("\n".join(gitignore_entries) + "\n")
        print("Created .gitignore with linting-related entries")

    print("\nLinting and formatting setup complete!")
    print("\nTo use these tools:")
    print("1. Install pre-commit: pip install pre-commit")
    print("2. Install hooks: pre-commit install")
    print("3. Run manually: pre-commit run --all-files")
    print("\nAlternatively, run tools directly:")
    print("  ruff check . --config code/.ruff.toml")
    print("  black . --config code/.black.toml")

    return 0

if __name__ == "__main__":
    sys.exit(main())
