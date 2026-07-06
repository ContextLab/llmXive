"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script ensures the necessary configuration files exist in the project root
and provides a CLI entry point to run formatting and linting checks.
"""

import os
import subprocess
import sys
from pathlib import Path


def write_config_file(filepath: str, content: str) -> None:
    """Write configuration content to a file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {filepath}")


def setup_ruff_config() -> None:
    """Create .ruff.toml configuration."""
    content = """[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code"]
force-sort-within-sections = true

[format]
line-length = 88
"""
    write_config_file(".ruff.toml", content)


def setup_black_config() -> None:
    """Create .black.toml configuration."""
    content = """[tool.black]
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
"""
    write_config_file(".black.toml", content)


def run_format() -> None:
    """Run black formatter on the codebase."""
    try:
        result = subprocess.run(
            ["black", "."],
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        print(result.stdout)
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it via: pip install black")
        sys.exit(1)


def run_lint() -> None:
    """Run ruff linter on the codebase."""
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        print(result.stdout)
        print("Linting completed successfully (no issues found).")
    except subprocess.CalledProcessError as e:
        print(f"Linting found issues:\n{e.stdout}")
        # Exit with 0 for linting issues to allow CI to handle it, 
        # but for this script we might want to fail. 
        # Following standard CI practice: fail on lint errors.
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it via: pip install ruff")
        sys.exit(1)


def main() -> None:
    """Main entry point for the setup script."""
    if len(sys.argv) < 2:
        print("Usage: python setup_linting.py [format|lint|check]")
        print("  format: Run black formatter")
        print("  lint:   Run ruff linter")
        print("  check:  Run both (format then lint)")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "format":
        run_format()
    elif command == "lint":
        run_lint()
    elif command == "check":
        print("Running formatter...")
        run_format()
        print("Running linter...")
        run_lint()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()